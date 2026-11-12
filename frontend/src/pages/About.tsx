import "../styles/public.css"
import { PageHeader } from "../components/PageHeader"

export function About() {
  return (
    <div className="page narrow">
      <PageHeader
        eyebrow="Sobre"
        title="GameCompass conectado"
        lede="Jogos consultados na Steam e CPUs e GPUs lidas do catálogo no Neo4j."
      />
      <div className="about-panels">
        <section className="panel">
          <h2>Dados dos jogos</h2>
          <p>
          Pesquise seus jogos pelo nome e escolha suas âncoras. Títulos, capas, gêneros gerais e requisitos vêm da
          Steam. Categorias de jogabilidade como Plataforma, Roguelike, Tiro e Puzzle são complementadas
          pelo GameCompass. As sugestões são consultadas quando você solicitar.
        </p>
        </section>
        <section className="panel">
          <h2>Hardware</h2>
          <p>
          Escolha seu processador e sua placa de vídeo no catálogo. A comparação mostra se cada componente
          atende aos requisitos mínimos ou recomendados e sugere uma substituição quando há um requisito
          não atendido, com outras opções de fabricantes quando disponíveis. Informe também a RAM e
          o sistema operacional do computador.
        </p>
        </section>
        <section className="panel">
          <h2>Afinidade e validação</h2>
          <p>
          Cada jogo é comparado individualmente com suas âncoras e mostra quais características compartilha
          com elas. Ao mudar suas preferências, solicite uma nova busca. Requisitos ainda
          não identificados ficam pendentes. A comparação de hardware é uma aproximação do protótipo e
          não prevê FPS. No Windows, consideramos a versão principal informada no perfil.
        </p>
        </section>
        <section className="panel">
          <h2>Conta e perfil</h2>
          <p>
          A conta, o perfil e a configuração do computador ficam salvos no servidor e acompanham você em
          qualquer navegador. Esta é uma interface de teste do TCC, sem recuperação de senha por e-mail.
        </p>
        </section>
      </div>
    </div>
  )
}
