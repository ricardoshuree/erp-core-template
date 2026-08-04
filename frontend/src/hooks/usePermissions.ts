// [mcp-local harness] feature: rbac-crud-permission-matrix | plano: ca222723 | 2026-08-04 13:44:57
// 4 helpers CRUD (canCreate/canRead/canUpdate/canDelete) substituem canRead/canEdit
/**
 * usePermissions — busca as permissões efetivas do usuário logado.
 *
 * Consome GET /api/v1/users/me/permissions e retorna:
 *   - is_superuser: boolean
 *   - roles: string[]
 *   - permissions: { module, description, can_create, can_read, can_update, can_delete }[]
 *
 * Helpers:
 *   - canCreate(module) → true se o usuário pode criar no módulo
 *   - canRead(module)   → true se o usuário pode ler o módulo
 *   - canUpdate(module) → true se o usuário pode editar registros existentes
 *   - canDelete(module) → true se o usuário pode apagar
 *
 * Uso:
 *   const { canRead, canDelete } = usePermissions()
 *   if (canRead("clientes")) { ... }
 *   if (canDelete("clientes")) { ... } // ex: role "Gerente" tem create/read/update mas NÃO delete
 */

import { useQuery } from "@tanstack/react-query"
import { OpenAPI } from "@/client"
import { isLoggedIn } from "./useAuth"

export interface ModulePermission {
  module: string
  description: string | null
  can_create: boolean
  can_read: boolean
  can_update: boolean
  can_delete: boolean
}

export interface UserPermissions {
  is_superuser: boolean
  roles: string[]
  permissions: ModulePermission[]
}

async function fetchPermissions(): Promise<UserPermissions> {
  const token = localStorage.getItem("access_token")
  // Usa a mesma base URL configurada para o client OpenAPI (VITE_API_URL),
  // já que em produção o frontend (Vercel) e o backend (Railway) vivem em
  // domínios diferentes -- um caminho relativo bateria no próprio Vercel.
  const response = await fetch(`${OpenAPI.BASE}/api/v1/users/me/permissions`, {
    headers: { Authorization: `Bearer ${token}` },
  })
  if (!response.ok) throw new Error("Failed to fetch permissions")
  return response.json()
}

export function usePermissions() {
  const { data, isLoading, error } = useQuery<UserPermissions>({
    queryKey: ["userPermissions"],
    queryFn: fetchPermissions,
    enabled: isLoggedIn(),
    staleTime: 5 * 60 * 1000, // 5 minutos — permissões mudam raramente
  })

  const checkAction = (
    module: string,
    action: "can_create" | "can_read" | "can_update" | "can_delete",
  ): boolean => {
    if (!data) return false
    if (data.is_superuser) return true
    return data.permissions.some((p) => p.module === module && p[action])
  }

  const canCreate = (module: string): boolean => checkAction(module, "can_create")
  const canRead = (module: string): boolean => checkAction(module, "can_read")
  const canUpdate = (module: string): boolean => checkAction(module, "can_update")
  const canDelete = (module: string): boolean => checkAction(module, "can_delete")

  return {
    permissions: data,
    isLoading,
    error,
    canCreate,
    canRead,
    canUpdate,
    canDelete,
  }
}
