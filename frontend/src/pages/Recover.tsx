import { Link } from "react-router-dom"
import { AuthFrame } from "../components/AuthFrame"
import { useTitle } from "../components/PageHeader"

export function Recover() {
  useTitle("Recuperar senha")

  return (
    <AuthFrame
      title="Recuperar senha"
      lede="A redefinição por e-mail ainda não está disponível nesta versão."
    >
      <div className="stack">
        <p>
          Se você ainda está conectado em algum dispositivo, altere a senha em Conta, na seção Senha.
        </p>
        <p className="hint">
          Sem uma sessão aberta, não há como redefinir a senha agora: o envio de e-mail de recuperação está
          planejado para uma etapa futura. Você pode criar outra conta com um e-mail diferente.
        </p>
      </div>
      <p className="form-links">
        <Link to="/entrar">Voltar ao login</Link>
        <Link to="/cadastro">Criar conta</Link>
      </p>
    </AuthFrame>
  )
}
