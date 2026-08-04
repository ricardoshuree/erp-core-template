// [mcp-local harness] feature: rbac-permission-matrix-and-produtos-frontend | plano: bc499083 | 2026-08-04 14:14:53
// Modal com a matriz Role x Acao (checkboxes), grava via PUT /modules/{id}/permissions
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { Settings2 } from "lucide-react"
import { useEffect, useState } from "react"

import { type ModulePublic, ModulesService } from "@/client"
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
  DialogTrigger,
} from "@/components/ui/dialog"
import { LoadingButton } from "@/components/ui/loading-button"
import useCustomToast from "@/hooks/useCustomToast"
import { handleError } from "@/utils"

type ActionKey = "can_create" | "can_read" | "can_update" | "can_delete"

interface MatrixEntryState {
  role_id: string
  role_name: string
  can_create: boolean
  can_read: boolean
  can_update: boolean
  can_delete: boolean
}

interface PermissionMatrixDialogProps {
  module: ModulePublic
}

const ACTIONS: Array<{ key: ActionKey; label: string }> = [
  { key: "can_create", label: "Criar" },
  { key: "can_read", label: "Ver" },
  { key: "can_update", label: "Editar" },
  { key: "can_delete", label: "Apagar" },
]

const PermissionMatrixDialog = ({ module }: PermissionMatrixDialogProps) => {
  const [isOpen, setIsOpen] = useState(false)
  const [entries, setEntries] = useState<MatrixEntryState[]>([])
  const queryClient = useQueryClient()
  const { showSuccessToast, showErrorToast } = useCustomToast()

  const { data: matrix } = useQuery({
    queryKey: ["module-permissions", module.id],
    queryFn: () => ModulesService.readModulePermissions({ moduleId: module.id }),
    enabled: isOpen,
  })

  useEffect(() => {
    if (matrix) {
      setEntries(
        matrix.entries.map((e) => ({
          role_id: e.role_id,
          role_name: e.role_name,
          can_create: e.can_create,
          can_read: e.can_read,
          can_update: e.can_update,
          can_delete: e.can_delete,
        })),
      )
    }
  }, [matrix])

  const mutation = useMutation({
    mutationFn: () =>
      ModulesService.updateModulePermissions({
        moduleId: module.id,
        requestBody: {
          entries: entries.map((e) => ({
            role_id: e.role_id,
            can_create: e.can_create,
            can_read: e.can_read,
            can_update: e.can_update,
            can_delete: e.can_delete,
          })),
        },
      }),
    onSuccess: () => {
      showSuccessToast("Permissões atualizadas com sucesso")
      setIsOpen(false)
    },
    onError: handleError.bind(showErrorToast),
    onSettled: () => {
      queryClient.invalidateQueries({
        queryKey: ["module-permissions", module.id],
      })
      // Se o usuário logado tiver essa role, a mudança precisa refletir
      // no proprio menu lateral/permissoes dele tambem
      queryClient.invalidateQueries({ queryKey: ["userPermissions"] })
    },
  })

  const toggle = (roleId: string, action: ActionKey, checked: boolean) => {
    setEntries((prev) =>
      prev.map((e) => (e.role_id === roleId ? { ...e, [action]: checked } : e)),
    )
  }

  return (
    <Dialog open={isOpen} onOpenChange={setIsOpen}>
      <DialogTrigger asChild>
        <Button variant="outline" size="sm">
          <Settings2 className="mr-2 size-4" />
          Permissões
        </Button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-2xl">
        <DialogHeader>
          <DialogTitle className="capitalize">
            Permissões — {module.name}
          </DialogTitle>
          <DialogDescription>
            Marque o que cada role pode fazer neste módulo. Superusuários
            sempre têm acesso total, independente desta matriz.
          </DialogDescription>
        </DialogHeader>

        <div className="overflow-x-auto py-2">
          {!matrix && (
            <p className="text-sm text-muted-foreground">Carregando...</p>
          )}
          {matrix && (
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-muted-foreground">
                  <th className="pb-2 pr-4 font-medium">Role</th>
                  {ACTIONS.map((a) => (
                    <th
                      key={a.key}
                      className="pb-2 px-2 text-center font-medium"
                    >
                      {a.label}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {entries.map((entry) => (
                  <tr key={entry.role_id} className="border-t">
                    <td className="py-2 pr-4 font-medium capitalize">
                      {entry.role_name}
                    </td>
                    {ACTIONS.map((a) => (
                      <td key={a.key} className="py-2 px-2 text-center">
                        <Checkbox
                          checked={entry[a.key]}
                          onCheckedChange={(checked) =>
                            toggle(entry.role_id, a.key, checked === true)
                          }
                        />
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          )}
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
            disabled={!matrix}
          >
            Save
          </LoadingButton>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

export default PermissionMatrixDialog
