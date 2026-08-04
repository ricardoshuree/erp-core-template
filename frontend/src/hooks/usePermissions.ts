// [mcp-local harness] feature: fix-rbac-supabase-production-ready | plano: 509f25bf | 2026-08-04 07:25:33
// Corrige fetchPermissions para usar OpenAPI.BASE (VITE_API_URL) em vez de caminho relativo, ja que em producao frontend (Vercel) e backend (Railway) estao em dominios diferentes
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
import { OpenAPI } from "@/client"
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
