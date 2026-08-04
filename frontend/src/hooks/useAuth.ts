// [mcp-local harness] feature: supabase-auth-frontend | plano: 56185697 | 2026-08-04 00:43:00
// useAuth com loginWithGoogle e sincronizacao de sessao Supabase, mantendo login local intacto
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { useNavigate } from "@tanstack/react-router"
import { useEffect } from "react"

import {
  type Body_login_login_access_token as AccessToken,
  LoginService,
  type UserPublic,
  type UserRegister,
  UsersService,
} from "@/client"
import { supabase } from "@/lib/supabase"
import { handleError } from "@/utils"
import useCustomToast from "./useCustomToast"

const isLoggedIn = () => {
  return localStorage.getItem("access_token") !== null
}

// Sincroniza a sessão do Supabase (login Google) com o mesmo
// localStorage["access_token"] que o resto do app já usa (client
// OpenAPI, usePermissions, etc.) -- assim nenhum outro lugar do
// código precisa saber qual dos dois métodos de login foi usado.
//
// STATUS: não testado ponta a ponta -- precisa `bun install` para
// trazer @supabase/supabase-js, e um login Google real pra confirmar
// que o redirect e o onAuthStateChange disparam como esperado.
function useSupabaseSessionSync() {
  const navigate = useNavigate()

  useEffect(() => {
    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange((event, session) => {
      if (event === "SIGNED_IN" && session?.access_token) {
        localStorage.setItem("access_token", session.access_token)
        navigate({ to: "/" })
      }
      if (event === "SIGNED_OUT") {
        localStorage.removeItem("access_token")
      }
    })
    return () => subscription.unsubscribe()
  }, [navigate])
}

const useAuth = () => {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const { showErrorToast } = useCustomToast()

  useSupabaseSessionSync()

  const { data: user } = useQuery<UserPublic | null, Error>({
    queryKey: ["currentUser"],
    queryFn: UsersService.readUserMe,
    enabled: isLoggedIn(),
  })

  const signUpMutation = useMutation({
    mutationFn: (data: UserRegister) =>
      UsersService.registerUser({ requestBody: data }),
    onSuccess: () => {
      navigate({ to: "/login" })
    },
    onError: handleError.bind(showErrorToast),
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ["users"] })
    },
  })

  const login = async (data: AccessToken) => {
    const response = await LoginService.loginAccessToken({
      formData: data,
    })
    localStorage.setItem("access_token", response.access_token)
  }

  const loginMutation = useMutation({
    mutationFn: login,
    onSuccess: () => {
      navigate({ to: "/" })
    },
    onError: handleError.bind(showErrorToast),
  })

  const loginWithGoogle = async () => {
    await supabase.auth.signInWithOAuth({
      provider: "google",
      options: {
        redirectTo: window.location.origin,
      },
    })
    // Supabase redireciona pro Google e volta -- o resto acontece em
    // useSupabaseSessionSync() acima quando a sessão chegar.
  }

  const logout = () => {
    localStorage.removeItem("access_token")
    // Silencioso de propósito: se a sessão ativa era local (senha),
    // não existe sessão Supabase pra encerrar, e signOut() lida bem
    // com esse caso (não lança erro).
    supabase.auth.signOut()
    navigate({ to: "/login" })
  }

  return {
    signUpMutation,
    loginMutation,
    loginWithGoogle,
    logout,
    user,
  }
}

export { isLoggedIn }
export default useAuth
