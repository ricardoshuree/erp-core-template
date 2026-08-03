// [mcp-local harness] feature: frontend-rbac | plano: 3800c8da | 2026-08-03 15:41:19
// Hook usePermissions que busca /users/me/permissions com helpers canRead e canEdit
/**
 * usePermissions — busca as permissões efetivas do usuário logado.
 *
 * Consome GET /api/v1/users/me/permissions e retorna:
 *   - is_superuser: boolean
 *   - roles: string[]
 *   - permissions: { module, description, can_read, can_edit }[]
 *
 * Helpers:
 *   - canRead(module)  → true se o usuário pode ler o módulo
 *   - canEdit(module)  → true se o usuário pode editar o módulo
 *
 * Uso:
 *   const { canRead } = usePermissions()
 *   if (canRead("clientes")) { ... }
 */

import { useQuery } from "@tanstack/react-query"
import { isLoggedIn } from "./useAuth"

export interface ModulePermission {
  module: string
  description: string | null
  can_read: boolean
  can_edit: boolean
}

export interface UserPermissions {
  is_superuser: boolean
  roles: string[]
  permissions: ModulePermission[]
}

async function fetchPermissions(): Promise<UserPermissions> {
  const token = localStorage.getItem("access_token")
  const response = await fetch("/api/v1/users/me/permissions", {
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

  const canRead = (module: string): boolean => {
    if (!data) return false
    if (data.is_superuser) return true
    return data.permissions.some((p) => p.module === module && p.can_read)
  }

  const canEdit = (module: string): boolean => {
    if (!data) return false
    if (data.is_superuser) return true
    return data.permissions.some((p) => p.module === module && p.can_edit)
  }

  return {
    permissions: data,
    isLoading,
    error,
    canRead,
    canEdit,
  }
}
