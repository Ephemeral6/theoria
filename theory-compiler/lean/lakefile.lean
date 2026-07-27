import Lake
open Lake DSL

package «theoria-lean» where
  leanOptions := #[
    ⟨`autoImplicit, false⟩
  ]

@[default_target]
lean_lib «TheoriaLean» where
  srcDir := "."
  roots := #[`TheoriaLean]
