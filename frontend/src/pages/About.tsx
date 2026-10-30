import { PageHeader } from "../components/PageHeader"

export function About() {
  return (
    <div className="page narrow">
      <PageHeader
        eyebrow="Sobre"
        title="GameCompass conectado"
        lede="Jogos consultados na Steam e CPUs e GPUs lidas do catálogo no Neo4j."
      />
      <div className="prose">
        <h2>Dados dos jogos</h2>
        <p>
          Pesquise seus jogos pelo nome e escolha suas âncoras. Títulos, capas, gêneros e requisitos vêm da
          Steam. A interface começa sem catálogo de jogos. As sugestões são consultadas quando você solicitar.
        </p>
        <h2>Hardware</h2>
        <p>
          CPUs e GPUs usam o índice manual versionado do projeto. Uma peça conhecida sem nota ou um requisito
          não identificado permanece pendente. RAM e sistema operacional são opções locais; não recebem nós
          próprios no catálogo.
        </p>
        <h2>Afinidade e validação</h2>
        <p>
          As preferências usam gêneros e temáticas. A associação temática dos jogos será preenchida em uma
          etapa posterior; por enquanto a afinidade usa os gêneros e as âncoras. Requisitos incompletos e
          versão do sistema operacional ficam visíveis como pendências. A classificação manual é uma
          aproximação do TCC1.
        </p>
        <h2>Conta e perfil</h2>
        <p>
          A conta de teste, o perfil e a configuração do computador continuam salvos neste navegador. A
          autenticação de produção será integrada posteriormente.
        </p>
      </div>
    </div>
  )
}
