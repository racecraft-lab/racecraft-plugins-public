package main

import (
	"go/ast"
	"testing"
)

// Guard the extraction itself: clients own one HTTP destination, and the
// handler delegates evaluation without knowing whether another hop exists.
func TestChainPolicyHasOneOwner(t *testing.T) {
	fset, files, _ := backendProductionFiles(t)
	if files["client.go"] == nil || files["tools.go"] == nil {
		t.Fatal("missing client or tool source")
	}
	foundClient := false
	ast.Inspect(files["client.go"], func(node ast.Node) bool {
		spec, ok := node.(*ast.TypeSpec)
		if !ok || spec.Name.Name != "Client" {
			return true
		}
		foundClient = true
		fields := spec.Type.(*ast.StructType).Fields.List
		for _, field := range fields {
			for _, name := range field.Names {
				switch name.Name {
				case "Fallback", "switched", "Log":
					t.Errorf("%s: Client retains chain state %s", fset.Position(name.Pos()), name.Name)
				}
			}
		}
		return false
	})
	if !foundClient {
		t.Fatal("no Client declaration was checked")
	}
	ast.Inspect(files["tools.go"], func(node ast.Node) bool {
		if field, ok := node.(*ast.SelectorExpr); ok && field.Sel.Name == "Fallback" {
			t.Errorf("%s: tool handler still knows about a fallback", fset.Position(field.Pos()))
		}
		return true
	})
}
