// [mcp-local harness] feature: close-open-signup-security | plano: ac575558 | 2026-08-04 11:30:25
// Remove comentario desatualizado de 'nao testado'
// Cliente Supabase para o frontend -- usado só para autenticação
// (login Google via OAuth). Toda a leitura/escrita de dados de negócio
// continua indo pelo backend FastAPI (client/ gerado do OpenAPI), não
// direto pelo Supabase.
//
// Precisa de VITE_SUPABASE_URL e VITE_SUPABASE_ANON_KEY no .env do
// frontend (mesmos valores públicos usados no backend, prefixados com
// VITE_ para o Vite expor no bundle do browser -- são seguros de expor,
// é a "publishable key").
import { createClient } from "@supabase/supabase-js"

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY

if (!supabaseUrl || !supabaseAnonKey) {
  console.warn(
    "VITE_SUPABASE_URL / VITE_SUPABASE_ANON_KEY não configurados -- login com Google não vai funcionar.",
  )
}

export const supabase = createClient(supabaseUrl ?? "", supabaseAnonKey ?? "")
