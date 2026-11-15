package main

import (
	"encoding/json"
	"fmt"
	"go/ast"
	"go/constant"
	"go/importer"
	"go/parser"
	"go/token"
	"go/types"
	"io"
	"os"
	"os/exec"
	"reflect"
	"strings"
	"sync"
	"testing"
)

// Production code outside config.go consumes capabilities, never provider
// identities. Tests may still name providers to assert their contracts.
func TestProviderNamesStayInBackendSpecOwner(t *testing.T) {
	fset, files, info := backendProductionFiles(t)
	for name, file := range files {
		if name == "config.go" {
			continue
		}
		for _, pos := range providerNameComparisons(file, info) {
			t.Errorf("%s: provider-name comparison outside backend-spec owner config.go", fset.Position(pos))
		}
	}
}

// Parse every production file, including the owner for package-wide type
// resolution. A missing or malformed source set fails the gates.
func backendProductionFiles(t *testing.T) (*token.FileSet, map[string]*ast.File, *types.Info) {
	t.Helper()
	entries, err := os.ReadDir(".")
	if err != nil {
		t.Fatal(err)
	}
	fset := token.NewFileSet()
	files := map[string]*ast.File{}
	for _, entry := range entries {
		name := entry.Name()
		if !strings.HasSuffix(name, ".go") || strings.HasSuffix(name, "_test.go") {
			continue
		}
		file, err := parser.ParseFile(fset, name, nil, 0)
		if err != nil {
			t.Fatal(err)
		}
		files[name] = file
	}
	if len(files) == 0 {
		t.Fatal("no production source files found")
	}
	var sources []*ast.File
	for _, file := range files {
		sources = append(sources, file)
	}
	imp, err := backendExportImporter()
	if err != nil {
		t.Fatal(err)
	}
	return fset, files, checkedBackendTypes(t, fset, sources, imp)
}

// go list supplies the export data already built by go test, so go/types
// resolves the whole module without another dependency or a network lookup.
var backendExportImporter = sync.OnceValues(func() (types.Importer, error) {
	cmd := exec.Command("go", "list", "-deps", "-export", "-json", ".")
	cmd.Env = append(os.Environ(), "GOPROXY=off", "GOSUMDB=off")
	output, err := cmd.Output()
	if err != nil {
		return nil, fmt.Errorf("load backend type exports: %w", err)
	}
	exports := map[string]string{}
	decoder := json.NewDecoder(strings.NewReader(string(output)))
	for {
		var pkg struct{ ImportPath, Export string }
		if err := decoder.Decode(&pkg); err != nil {
			if err == io.EOF {
				break
			}
			return nil, err
		}
		exports[pkg.ImportPath] = pkg.Export
	}
	return importer.ForCompiler(token.NewFileSet(), "gc", func(path string) (io.ReadCloser, error) {
		export := exports[path]
		if export == "" {
			return nil, fmt.Errorf("missing backend type export for %s", path)
		}
		return os.Open(export)
	}), nil
})

func checkedBackendTypes(t *testing.T, fset *token.FileSet, files []*ast.File, imp types.Importer) *types.Info {
	t.Helper()
	info := &types.Info{
		Types:      map[ast.Expr]types.TypeAndValue{},
		Selections: map[*ast.SelectorExpr]*types.Selection{},
		Uses:       map[*ast.Ident]types.Object{},
	}
	cfg := types.Config{Importer: imp}
	if _, err := cfg.Check("backend", fset, files, info); err != nil {
		t.Fatalf("type-check backend ownership sources: %v", err)
	}
	return info
}

func providerNameComparisons(file *ast.File, info *types.Info) []token.Pos {
	var found []token.Pos
	seen := map[*ast.Object]bool{}
	var isProvider func(ast.Expr) bool
	isProvider = func(expr ast.Expr) bool {
		value := info.Types[expr].Value
		if value != nil && value.Kind() == constant.String {
			if _, ok := providers[constant.StringVal(value)]; ok {
				return true
			}
		}
		for {
			paren, ok := expr.(*ast.ParenExpr)
			if !ok {
				break
			}
			expr = paren.X
		}
		// go/types links package variables to their initializers across files.
		if id, ok := expr.(*ast.Ident); ok {
			for _, init := range info.InitOrder {
				if len(init.Lhs) == 1 && init.Lhs[0] == info.Uses[id] {
					return isProvider(init.Rhs)
				}
			}
		}
		// The AST links local variable aliases to their initializers. Constant
		// aliases are resolved by go/types above.
		if id, ok := expr.(*ast.Ident); ok && id.Obj != nil && !seen[id.Obj] {
			seen[id.Obj] = true
			defer delete(seen, id.Obj)
			switch decl := id.Obj.Decl.(type) {
			case *ast.AssignStmt:
				for i, lhs := range decl.Lhs {
					if name, ok := lhs.(*ast.Ident); ok && name.Name == id.Name && i < len(decl.Rhs) {
						return isProvider(decl.Rhs[i])
					}
				}
			case *ast.ValueSpec:
				for i, name := range decl.Names {
					if name.Name == id.Name && i < len(decl.Values) {
						return isProvider(decl.Values[i])
					}
				}
			}
		}
		selector, ok := expr.(*ast.SelectorExpr)
		if !ok {
			return false
		}
		selection := info.Selections[selector]
		if selection == nil || selection.Obj().Name() != "Name" {
			return false
		}
		recv := selection.Recv()
		if pointer, ok := recv.(*types.Pointer); ok {
			recv = pointer.Elem()
		}
		named, ok := recv.(*types.Named)
		return ok && named.Obj().Name() == "ProviderSpec"
	}
	ast.Inspect(file, func(node ast.Node) bool {
		switch n := node.(type) {
		case *ast.IndexExpr:
			if isProvider(n.Index) {
				found = append(found, n.Pos())
			} else if literal, ok := n.X.(*ast.CompositeLit); ok {
				for _, element := range literal.Elts {
					if pair, ok := element.(*ast.KeyValueExpr); ok && isProvider(pair.Key) {
						found = append(found, n.Pos())
						break
					}
				}
			}
		case *ast.CallExpr:
			fun := n.Fun
			switch generic := fun.(type) {
			case *ast.IndexExpr:
				fun = generic.X
			case *ast.IndexListExpr:
				fun = generic.X
			}
			callee, ok := fun.(*ast.SelectorExpr)
			if !ok {
				break
			}
			object := info.Uses[callee.Sel]
			if object == nil || object.Pkg() == nil {
				break
			}
			comparison := false
			switch object.Pkg().Path() + "." + object.Name() {
			case "strings.EqualFold", "strings.Compare", "strings.Contains", "strings.HasPrefix", "strings.HasSuffix", "strings.Index", "slices.Contains", "slices.Index":
				comparison = true
			}
			if comparison {
				for _, arg := range n.Args {
					matched := false
					ast.Inspect(arg, func(child ast.Node) bool {
						if expr, ok := child.(ast.Expr); ok && isProvider(expr) {
							matched = true
						}
						return !matched
					})
					if matched {
						found = append(found, n.Pos())
						break
					}
				}
			}
		case *ast.BinaryExpr:
			if (n.Op == token.EQL || n.Op == token.NEQ) && (isProvider(n.X) || isProvider(n.Y)) {
				found = append(found, n.Pos())
			}
		case *ast.SwitchStmt:
			if n.Tag != nil {
				if isProvider(n.Tag) {
					found = append(found, n.Tag.Pos())
					break
				}
				for _, stmt := range n.Body.List {
					clause := stmt.(*ast.CaseClause)
					for _, value := range clause.List {
						if isProvider(value) {
							found = append(found, value.Pos())
						}
					}
				}
			}
		}
		return true
	})
	return found
}

func TestProviderNameGateDetectsComparisons(t *testing.T) {
	for _, tc := range []struct {
		body string
		want int
	}{
		{`if spec.Name == "typesafe" {}`, 1},
		{`if ("openrouter") != spec.Name {}`, 1},
		{"switch name { case `typesafe`, \"openrouter\": }", 2},
		{`switch { case name == "typesafe": }`, 1},
		{`switch spec.Name { case name: }`, 1},
		{`_ = map[string]int{"typesafe": 1}[spec.Name]`, 1},
		{`_ = map[string]int{"typesafe": 1}[name]`, 1},
		{`const backend = "typesafe"; if name == backend {}`, 1},
		{`backend := "openrouter"; switch name { case backend: }`, 1},
		{`const backend = "type" + "safe"; if name != backend {}`, 1},
		{`local := "typesafe"; _ = local`, 0},
		{`if model == "typesafe/jev-1.13" {}`, 0},
	} {
		fset := token.NewFileSet()
		file, err := parser.ParseFile(fset, "fixture.go", "package fixture; type ProviderSpec struct { Name string }; func check(spec ProviderSpec, name, model string) { "+tc.body+" }", 0)
		if err != nil {
			t.Fatal(err)
		}
		info := checkedBackendTypes(t, fset, []*ast.File{file}, nil)
		if got := len(providerNameComparisons(file, info)); got != tc.want {
			t.Errorf("%s: found %d comparisons, want %d", tc.body, got, tc.want)
		}
	}
}

func TestProviderNameGateDetectsCrossFileComparisons(t *testing.T) {
	fset := token.NewFileSet()
	owner, err := parser.ParseFile(fset, "config.go", `package fixture
const providerTypeSafe = "typesafe"
var other = "typesafe"
type ProviderSpec struct { Name string }
var providers = map[string]ProviderSpec{"typesafe": {Name: "typesafe"}}
`, 0)
	if err != nil {
		t.Fatal(err)
	}
	for _, body := range []string{
		`if spec.Name == providerTypeSafe {}`,
		`if spec.Name == providers["typesafe"].Name {}`,
		`if name == other {}`,
	} {
		file, err := parser.ParseFile(fset, "images.go", "package fixture; func check(spec ProviderSpec, name string) { "+body+" }", 0)
		if err != nil {
			t.Fatal(err)
		}
		info := checkedBackendTypes(t, fset, []*ast.File{owner, file}, nil)
		if len(providerNameComparisons(file, info)) == 0 {
			t.Errorf("gate missed cross-file comparison: %s", body)
		}
	}
}

func TestProviderNameGateDetectsPredicateComparisons(t *testing.T) {
	imp, err := backendExportImporter()
	if err != nil {
		t.Fatal(err)
	}
	for _, body := range []string{
		`_ = text.EqualFold(spec.Name, "typesafe")`,
		`_ = text.Compare(spec.Name, name)`,
		`_ = slices.Contains([]string{"typesafe"}, name)`,
		`_ = slices.Contains[[]string, string]([]string{"typesafe"}, name)`,
	} {
		fset := token.NewFileSet()
		file, err := parser.ParseFile(fset, "fixture.go", `package fixture
import (text "strings"; "slices")
type ProviderSpec struct { Name string }
func check(spec ProviderSpec, name string) {
_ = text.Compare; _ = slices.Contains[[]string, string]
`+body+" }", 0)
		if err != nil {
			t.Fatal(err)
		}
		info := checkedBackendTypes(t, fset, []*ast.File{file}, imp)
		if len(providerNameComparisons(file, info)) == 0 {
			t.Errorf("gate missed predicate comparison: %s", body)
		}
	}
}

func TestWireFormatSelectionStaysInImages(t *testing.T) {
	fset, files, _ := backendProductionFiles(t)
	for name, file := range files {
		if name == "images.go" || name == "config.go" {
			continue
		}
		ast.Inspect(file, func(node ast.Node) bool {
			if selector, ok := node.(*ast.SelectorExpr); ok && selector.Sel.Name == "WireFormat" {
				t.Errorf("%s: only images.go may choose a wire format", fset.Position(selector.Pos()))
			}
			return true
		})
	}
}

func TestBackendSpecLimitsAreComplete(t *testing.T) {
	if len(providers) == 0 {
		t.Fatal("no backend rows")
	}
	for name, spec := range providers {
		t.Run(name, func(t *testing.T) {
			for _, problem := range backendLimitProblems(reflect.ValueOf(spec)) {
				t.Error(problem)
			}
		})
	}
}

func backendLimitProblems(spec reflect.Value) []string {
	var problems []string
	var check func(reflect.Value, string)
	check = func(value reflect.Value, path string) {
		switch value.Kind() {
		case reflect.Struct:
			for i := 0; i < value.NumField(); i++ {
				check(value.Field(i), path+"."+value.Type().Field(i).Name)
			}
		case reflect.Int:
			if value.Int() == 0 || value.Int() < -1 {
				problems = append(problems, path+": limit must be positive or explicit no-limit (-1), never zero")
			}
		default:
			problems = append(problems, path+": unknown limit shape")
		}
	}
	for _, name := range []string{"Limits", "ImageLimits", "RequestTokens", "QuestionTokens", "LongContextTokens"} {
		value := spec.FieldByName(name)
		if !value.IsValid() {
			problems = append(problems, name+": missing backend limits")
			continue
		}
		check(value, name)
	}
	return problems
}

// Every integer limit, including fields added later, is checked. Prove the
// completeness gate fails closed by clearing each field in a copied row.
func TestBackendSpecCompletenessRejectsEveryZeroLimit(t *testing.T) {
	for name, spec := range providers {
		original := reflect.ValueOf(spec)
		var clearEach func(reflect.Value, []int, string)
		clearEach = func(value reflect.Value, indexes []int, path string) {
			if value.Kind() == reflect.Struct {
				for i := 0; i < value.NumField(); i++ {
					clearEach(value.Field(i), append(append([]int{}, indexes...), i), path+"."+value.Type().Field(i).Name)
				}
				return
			}
			t.Run(name+"/"+path, func(t *testing.T) {
				copy := reflect.New(original.Type()).Elem()
				copy.Set(original)
				copy.FieldByIndex(indexes).SetInt(0)
				if len(backendLimitProblems(copy)) == 0 {
					t.Fatal("completeness gate accepted a zero limit")
				}
			})
		}
		for i := 0; i < original.NumField(); i++ {
			field := original.Type().Field(i).Name
			switch field {
			case "Limits", "ImageLimits", "RequestTokens", "QuestionTokens", "LongContextTokens":
				clearEach(original.Field(i), []int{i}, field)
			}
		}
	}
}
