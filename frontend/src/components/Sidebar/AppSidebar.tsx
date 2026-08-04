// [mcp-local harness] feature: rbac-permission-matrix-sidebar | plano: 23d4f034 | 2026-08-04 14:59:40
// Adiciona item de menu Permissoes, mantem Items original
/**
 * AppSidebar — menu lateral dinâmico por módulo/role.
 *
 * Itens fixos (sempre visíveis para usuários autenticados):
 *   - Dashboard
 *
 * Itens controlados por módulo (visíveis se can_read):
 *   - Items        → módulo "items"  (exemplo do template original)
 *   - Usuários     → módulo "usuarios"
 *   - Configurações → módulo "configuracoes"
 *
 * Itens exclusivos de superuser:
 *   - Admin        → apenas is_superuser
 *   - Permissões   → apenas is_superuser (matriz Role x Módulo x Ação CRUD)
 *
 * Para adicionar um novo módulo num ERP filho:
 *   1. Cadastre o módulo no banco (migration ou seed)
 *   2. Adicione uma entrada em MODULE_ITEMS abaixo com o mesmo nome de módulo
 *   3. O menu aparece automaticamente para quem tiver permissão
 *   4. Configure a matriz de permissões desse módulo em /permissions
 */

import {
  Briefcase,
  Home,
  Package,
  Settings,
  ShieldCheck,
  Users,
} from "lucide-react"

import { SidebarAppearance } from "@/components/Common/Appearance"
import { Logo } from "@/components/Common/Logo"
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarHeader,
} from "@/components/ui/sidebar"
import useAuth from "@/hooks/useAuth"
import { usePermissions } from "@/hooks/usePermissions"
import { type Item, Main } from "./Main"
import { User } from "./User"

// Itens sempre visíveis para qualquer usuário autenticado
const FIXED_ITEMS: Item[] = [
  { icon: Home, title: "Dashboard", path: "/" },
]

// Mapeamento de módulo → item de menu
// O campo "module" deve coincidir exatamente com o nome do módulo no banco
const MODULE_ITEMS: Array<Item & { module: string }> = [
  { module: "items",         icon: Briefcase, title: "Items",         path: "/items" },
  { module: "usuarios",      icon: Users,     title: "Usuários",      path: "/admin" },
  { module: "configuracoes", icon: Settings,  title: "Configurações", path: "/settings" },
]

// Itens exclusivos de superuser (acesso administrativo completo)
const ADMIN_ITEM: Item = { icon: Package, title: "Admin", path: "/admin" }
const PERMISSIONS_ITEM: Item = { icon: ShieldCheck, title: "Permissões", path: "/permissions" }

export function AppSidebar() {
  const { user: currentUser } = useAuth()
  const { canRead, isLoading } = usePermissions()

  // Monta os itens de menu de acordo com as permissões
  const moduleItems: Item[] = isLoading
    ? [] // não mostra nada enquanto carrega — evita flash de itens
    : MODULE_ITEMS.filter((item) => canRead(item.module))

  const items: Item[] = [
    ...FIXED_ITEMS,
    ...moduleItems,
    ...(currentUser?.is_superuser ? [ADMIN_ITEM, PERMISSIONS_ITEM] : []),
  ]

  return (
    <Sidebar collapsible="icon">
      <SidebarHeader className="px-4 py-6 group-data-[collapsible=icon]:px-0 group-data-[collapsible=icon]:items-center">
        <Logo variant="responsive" />
      </SidebarHeader>
      <SidebarContent>
        <Main items={items} />
      </SidebarContent>
      <SidebarFooter>
        <SidebarAppearance />
        <User user={currentUser} />
      </SidebarFooter>
    </Sidebar>
  )
}

export default AppSidebar
