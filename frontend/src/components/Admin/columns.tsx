// [mcp-local harness] feature: fix-roles-possibly-undefined | plano: fb100a71 | 2026-08-04 12:46:38
// Fallback para array vazio quando roles vier undefined
import type { ColumnDef } from "@tanstack/react-table"

import type { UserPublicWithRoles } from "@/client"
import { Badge } from "@/components/ui/badge"
import { cn } from "@/lib/utils"
import { UserActionsMenu } from "./UserActionsMenu"

export type UserTableData = UserPublicWithRoles & {
  isCurrentUser: boolean
}

export const columns: ColumnDef<UserTableData>[] = [
  {
    accessorKey: "full_name",
    header: "Full Name",
    cell: ({ row }) => {
      const fullName = row.original.full_name
      return (
        <div className="flex items-center gap-2">
          <span
            className={cn("font-medium", !fullName && "text-muted-foreground")}
          >
            {fullName || "N/A"}
          </span>
          {row.original.isCurrentUser && (
            <Badge variant="outline" className="text-xs">
              You
            </Badge>
          )}
        </div>
      )
    },
  },
  {
    accessorKey: "email",
    header: "Email",
    cell: ({ row }) => (
      <span className="text-muted-foreground">{row.original.email}</span>
    ),
  },
  {
    accessorKey: "is_superuser",
    // Tipo de acesso (superuser vs. usuário comum) -- NÃO confundir
    // com as roles RBAC (coluna "Roles" abaixo, controla permissão
    // por módulo). Superuser ignora RBAC e acessa tudo.
    header: "Tipo",
    cell: ({ row }) => (
      <Badge variant={row.original.is_superuser ? "default" : "secondary"}>
        {row.original.is_superuser ? "Superuser" : "User"}
      </Badge>
    ),
  },
  {
    accessorKey: "roles",
    header: "Roles",
    cell: ({ row }) => {
      const roles = row.original.roles ?? []
      if (roles.length === 0) {
        return <span className="text-xs text-muted-foreground">—</span>
      }
      return (
        <div className="flex flex-wrap gap-1">
          {roles.map((role) => (
            <Badge key={role} variant="outline" className="text-xs capitalize">
              {role}
            </Badge>
          ))}
        </div>
      )
    },
  },
  {
    accessorKey: "is_active",
    header: "Status",
    cell: ({ row }) => (
      <div className="flex items-center gap-2">
        <span
          className={cn(
            "size-2 rounded-full",
            row.original.is_active ? "bg-green-500" : "bg-gray-400",
          )}
        />
        <span className={row.original.is_active ? "" : "text-muted-foreground"}>
          {row.original.is_active ? "Active" : "Inactive"}
        </span>
      </div>
    ),
  },
  {
    id: "actions",
    header: () => <span className="sr-only">Actions</span>,
    cell: ({ row }) => (
      <div className="flex justify-end">
        <UserActionsMenu user={row.original} />
      </div>
    ),
  },
]
