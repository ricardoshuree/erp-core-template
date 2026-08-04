// [mcp-local harness] feature: fix-roles-possibly-undefined | plano: fb100a71 | 2026-08-04 12:47:00
// Fallback para array vazio quando user.roles vier undefined
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { ShieldCheck } from "lucide-react"
import { useEffect, useState } from "react"

import { type UserPublicWithRoles, RolesService, UsersService } from "@/client"
import { Button } from "@/components/ui/button"
import { Checkbox } from "@/components/ui/checkbox"
import {
  Dialog,
  DialogClose,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { DropdownMenuItem } from "@/components/ui/dropdown-menu"
import { LoadingButton } from "@/components/ui/loading-button"
import useCustomToast from "@/hooks/useCustomToast"
import { handleError } from "@/utils"

interface ManageRolesProps {
  user: UserPublicWithRoles
  onSuccess: () => void
}

const ManageRoles = ({ user, onSuccess }: ManageRolesProps) => {
  const [isOpen, setIsOpen] = useState(false)
  const [selectedRoleIds, setSelectedRoleIds] = useState<string[]>([])
  const queryClient = useQueryClient()
  const { showSuccessToast, showErrorToast } = useCustomToast()

  const { data: roles } = useQuery({
    queryKey: ["roles"],
    queryFn: () => RolesService.readRoles(),
    enabled: isOpen,
  })

  // Ao abrir o modal, marca os checkboxes das roles que o usuário já tem
  // (casando por nome, já que a listagem de usuários só traz os nomes)
  useEffect(() => {
    if (isOpen && roles) {
      const userRoles = user.roles ?? []
      const currentRoleIds = roles.data
        .filter((role) => userRoles.includes(role.name))
        .map((role) => role.id)
      setSelectedRoleIds(currentRoleIds)
    }
  }, [isOpen, roles, user.roles])

  const mutation = useMutation({
    mutationFn: () =>
      UsersService.updateUserRoles({
        userId: user.id,
        requestBody: { role_ids: selectedRoleIds },
      }),
    onSuccess: () => {
      showSuccessToast("Roles atualizadas com sucesso")
      setIsOpen(false)
      onSuccess()
    },
    onError: handleError.bind(showErrorToast),
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ["users"] })
    },
  })

  const toggleRole = (roleId: string, checked: boolean) => {
    setSelectedRoleIds((prev) =>
      checked ? [...prev, roleId] : prev.filter((id) => id !== roleId),
    )
  }

  return (
    <Dialog open={isOpen} onOpenChange={setIsOpen}>
      <DropdownMenuItem
        onSelect={(e) => e.preventDefault()}
        onClick={() => setIsOpen(true)}
      >
        <ShieldCheck />
        Manage Roles
      </DropdownMenuItem>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Manage Roles — {user.email}</DialogTitle>
          <DialogDescription>
            Roles RBAC controlam acesso por módulo (ex: "vendas",
            "estoque"). Independente do controle "Superuser", que dá
            acesso irrestrito ignorando roles.
          </DialogDescription>
        </DialogHeader>

        <div className="grid gap-3 py-4">
          {!roles && (
            <p className="text-sm text-muted-foreground">Carregando roles...</p>
          )}
          {roles?.data.length === 0 && (
            <p className="text-sm text-muted-foreground">
              Nenhuma role cadastrada ainda.
            </p>
          )}
          {roles?.data.map((role) => (
            <div key={role.id} className="flex items-start gap-3">
              <Checkbox
                id={`role-${role.id}`}
                checked={selectedRoleIds.includes(role.id)}
                onCheckedChange={(checked) =>
                  toggleRole(role.id, checked === true)
                }
              />
              <label htmlFor={`role-${role.id}`} className="grid gap-0.5">
                <span className="text-sm font-medium leading-none capitalize">
                  {role.name}
                </span>
                {role.description && (
                  <span className="text-xs text-muted-foreground">
                    {role.description}
                  </span>
                )}
              </label>
            </div>
          ))}
        </div>

        <DialogFooter>
          <DialogClose asChild>
            <Button variant="outline" disabled={mutation.isPending}>
              Cancel
            </Button>
          </DialogClose>
          <LoadingButton
            onClick={() => mutation.mutate()}
            loading={mutation.isPending}
          >
            Save
          </LoadingButton>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

export default ManageRoles
