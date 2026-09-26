# Lumini

Um gravador de gameplay que guarda só o que você pediu: você joga, aperta **F8**
quando algo bom acontece, e o clipe do último minuto fica salvo. Depois você
abre a biblioteca, corta o que interessa e manda pro Discord — com um nome que
você reconhece, e num tamanho que caiba como anexo.

Não tem nuvem, não tem conta, não tem nada rodando fora da sua máquina.

---

## Instalar no Linux (CachyOS, KDE Plasma)

```bash
git clone https://github.com/otowm/lume-lumini.git lumini
cd lumini
./instalar-lumini.sh
```

O script confere o que falta antes de mexer em qualquer coisa e diz o nome do
pacote quando algo está ausente. Se ele reclamar de `gpu-screen-recorder` ou
`kdotool`, instale e rode de novo:

```bash
sudo pacman -S --needed ffmpeg libpulse libkscreen python tk
paru -S gpu-screen-recorder kdotool
```

Ao final ele diz `Lumini instalado`. Se avisar que você **não está no grupo
`input`**, rode o comando que ele mostra e reabra a sessão — sem isso o toque no
F8 funciona, mas *segurar* o F8 não é percebido.

## Instalar no Windows

1. Instale o [Python](https://www.python.org/downloads/) marcando **"Add
   python.exe to PATH"**. Use o do site, não o da Microsoft Store.
2. Instale o [OBS Studio](https://obsproject.com). É ele que grava, mas você
   nunca vai precisar abri-lo: o Lumini faz uma cópia própria e cuida de tudo.
3. Instale o ffmpeg: `winget install Gyan.FFmpeg` no PowerShell.
4. Baixe o projeto (o botão **Code → Download ZIP** do GitHub serve) e, na pasta:

```powershell
powershell -ExecutionPolicy Bypass -File instalar-lumini.ps1
```

Você ganha um atalho na Área de Trabalho e o Lumini passa a subir junto com o
Windows — o que é necessário, porque no Windows o gravador funciona por dentro do
app. **A primeira gravação demora alguns minutos**: é o Lumini fazendo sua cópia
do OBS (~475 MB). Só a primeira.

---

## Usar

A interface abre em **http://127.0.0.1:8876** — e também no endereço da sua
máquina na rede, que o instalador mostra no final (ver "Abrir de outro aparelho").

**1. Diga quais jogos gravar.** Ajustes → Vídeo seletivo. A lista já vem com
alguns; cada linha é um pedaço do nome da janela do jogo. No modo avançado há um
botão "Testar janela": clique, troque para o jogo em 3 segundos, e ele diz se
gravaria ou não.

**2. Escolha como gravar.**

- **Clipes (F8)** — nada vai para o disco até você pedir. O gravador mantém o
  último minuto em memória, e o F8 salva esse minuto. É o modo para jogar sem
  encher o HD.
- **Contínuo** — grava a sessão inteira enquanto o jogo estiver em foco.

**3. Jogue.** Uma faixa fina aparece no canto da tela (a HUD) mostrando que está
gravando, e cada ação toca um som de confirmação.

| No modo Clipes | Faz |
|---|---|
| **Tocar F8** | salva o último minuto |
| **Tocar F8 de novo, dentro do mesmo minuto** | *estende* o mesmo clipe, em vez de criar outro |
| **Segurar F8** | começa a gravar tudo dali em diante, com o minuto anterior emendado na frente; segure de novo para fechar |

**4. Ache e mande.** Na biblioteca, cada clipe tem miniatura, hora e duração.
O botão **Enviar** abre tudo o que você precisa:

- **Baixar** — o arquivo com nome legível (`2026-09-26 00-10 Sea of
  Thieves.mp4`), direto na sua pasta de downloads.
- **Versão leve** — recodifica para caber no limite de anexo do Discord (20 MB
  por padrão). Vai com uma faixa de áudio só, a mixagem.
- **Gerar link** — quando nem comprimido cabe. Sobe para um host grátis e
  devolve um link para colar no chat. O link é **público**: quem tiver o
  endereço assiste. Por padrão expira em 3 dias.

Para cortar, abra o clipe e use o **✂** no player: arraste as bordas e salve.

## Abrir de outro aparelho

Já vem assim: além do `127.0.0.1`, a interface responde no endereço da sua
máquina na rede — o instalador mostra quais são, e dá para abrir a biblioteca do
celular, do notebook ou do PC do amigo pelo navegador. No Windows, na primeira
vez, o próprio Windows pergunta se libera o acesso na rede; responda que sim.

Funciona em qualquer rede doméstica, e continua funcionando se o seu endereço
mudar (trocar de Wi-Fi, reiniciar o roteador) — é de propósito, para não parar de
abrir sem motivo aparente.

**Não há senha.** Quem estiver na mesma rede e abrir o endereço vê a sua
biblioteca e baixa os seus clipes. Em casa isso costuma ser o que se quer; num
Wi-Fi de faculdade, de trabalho ou de café, não. Para fechar só nesta máquina:

```bash
./instalar-lumini.sh --somente-local      # Linux
```

No Windows, rode `setx LUME_BIND_HOST 127.0.0.1` e saia e entre novamente na
sessão do Windows. Isso vale também para a inicialização automática. Para
reabrir na rede, use `setx LUME_BIND_HOST 0.0.0.0` e entre novamente.
No Linux, para limitar a uma faixa só sua, em vez de todas as privadas:
`./instalar-lumini.sh --rede 192.168.0.0/24`.

---

## As três faixas de áudio

O Lumini grava seu microfone, o áudio do Discord e o som do jogo em **faixas
separadas** dentro do mesmo arquivo. Serve para, depois, abaixar sua própria voz
ou tirar a conversa dos amigos antes de postar. No player há um mixer com um
controle por faixa.

No Linux isso depende de o áudio do Discord passar pelo bus certo. O instalador
tenta ligar sozinho; se a faixa do Discord sair muda, abra o Discord, entre numa
chamada e rode:

```bash
~/bin/audio-bus.sh discord
```

Se ele não achar o Discord, vai listar o que está tocando — se o seu Discord
aparecer com outro nome (Vesktop, ou no navegador), ponha esse nome no
`~/.config/captura-dia/video.conf`:

```
DISCORD_NODE_PATTERN='o nome que apareceu'
```

---

## Onde ficam os arquivos

Tudo dentro de uma pasta só, que você escolhe em Ajustes → Armazenamento
(padrão: `~/lumini` no Linux, `~/captura-dia` no Windows):

- `video-buffer/` — os clipes gravados
- `clips/` — os que você marcou como preservados
- `edicao/` — atalhos com nome legível, para abrir no editor
- `lume.sqlite3` — o índice (marcadores, sessões, links gerados)

Apagar um clipe pela interface apaga o arquivo. Nada é enviado para fora da sua
máquina, exceto quando **você** clica em "Gerar link".

---

## Não gravou. E agora?

**A HUD não aparece e nada é salvo.** Confira se o jogo casa com a lista:
Ajustes → Vídeo seletivo → modo avançado → "Testar janela". Se disser "não
gravaria", acrescente um pedaço do nome da janela na lista.

**O F8 não faz nada.** No Linux, confira se você está no grupo `input`
(`groups | grep input`); sem ele, só o *toque* funciona, e pelo atalho do KDE.
No Windows, o F8 pode estar tomado por outro programa — troque o atalho em
Ajustes → Vídeo seletivo.

**O clipe saiu sem som, ou faltando uma faixa.** Rode
`~/bin/audio-bus.sh status` (Linux) e veja se `MicBus`, `DiscordBus` e
`RecordBus` existem. Se não, `~/bin/audio-bus.sh ensure`.

**Parou de gravar no meio.** No Linux, o que aconteceu está aqui:

```bash
journalctl --user -u captura-dia-video -n 100
```

Se precisar pedir ajuda, mande essa saída junto — é onde o motivo aparece.
