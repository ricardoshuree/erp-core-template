// [mcp-local harness] feature: rbac-permission-matrix-and-produtos-frontend | plano: bc499083 | 2026-08-04 14:14:32
// Nova pagina /permissions -- lista modulos, cada um abre a matriz de permissoes
import { useSuspenseQuery } from "@tanstack/react-query"
import { createFileRoute, redirect } from "@tanstack/react-router"
import { Suspense } from "react"

import { ModulesService, UsersService } from "@/client"
import PermissionMatrixDialog from "@/components/Permissions/PermissionMatrixDialog"

function getModulesQueryOptions() {
  return {
    queryFn: () => ModulesService.readModules(),
    queryKey: ["modules"],
  }
}

export const Route = createFileRoute("/_layout/permissions")({
  component: Permissions,
  beforeLoad: async () => {
    const user = await UsersService.readUserMe()
    if (!user.is_superuser) {
      throw redirect({
        to: "/",
      })
    }
  },
  head: () => ({
    meta: [
      {
        title: "Permissões - FastAPI Template",
      },
    ],
  }),
})

function ModulesListContent() {
  const { data: modules } = useSuspenseQuery(getModulesQueryOptions())

  if (modules.data.length === 0) {
    return (
      <p className="text-muted-foreground">
        Nenhum módulo RBAC cadastrado ainda.
      </p>
    )
  }

  return (
    <div className="flex flex-col gap-2">
      {modules.data.map((module) => (
        <div
          key={module.id}
          className="flex items-center justify-between rounded-lg border px-4 py-3"
        >
          <div>
            <p className="font-medium capitalize">{module.name}</p>
            {module.description && (
              <p className="text-sm text-muted-foreground">
                {module.description}
              </p>
            )}
          </div>
          <PermissionMatrixDialog module={module} />
        </div>
      ))}
    </div>
  )
}

function Permissions() {
  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Permissões</h1>
        <p className="text-muted-foreground">
          Configure o que cada role pode criar, ver, editar e apagar em
          cada módulo. Superusuários sempre têm acesso total.
        </p>
      </div>
      <Suspense
        fallback={
          <p className="text-muted-foreground">Carregando módulos...</p>
        }
      >
        <ModulesListContent />
      </Suspense>
    </div>
  )
}
