package main

import (
	"go/ast"
	"testing"
)

// Credential parsing and hop selection each have one policy owner. This
// guards the consolidation without coupling behavior tests to private fields.
func TestResolutionPolicyHasOneOwner(t *testing.T) {
	fset, files, _ := backendProductionFiles(t)
	for name, file := range files {
		ast.Inspect(file, func(node ast.Node) bool {
			switch n := node.(type) {
			case *ast.CallExpr:
				if fn, ok := n.Fun.(*ast.Ident); ok {
					switch fn.Name {
					case "parseKey", "readKeyFile":
						if name != "auth.go" {
							t.Errorf("%s: credential loading must go through auth.go", fset.Position(n.Pos()))
						}
					case "resolveProvider", "resolveFallback":
						if name != "resolver.go" {
							t.Errorf("%s: hop resolution must go through resolver.go", fset.Position(n.Pos()))
						}
					}
				}
			case *ast.AssignStmt:
				for _, lhs := range n.Lhs {
					if field, ok := lhs.(*ast.SelectorExpr); ok && field.Sel.Name == "Fallback" && name != "resolver.go" {
						// Startup selection and initial client wiring share the
						// resolver; request execution stays in the existing runner.
						t.Errorf("%s: configured hop selection must go through resolver.go", fset.Position(n.Pos()))
					}
				}
			}
			return true
		})
	}
}
