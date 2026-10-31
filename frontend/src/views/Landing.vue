<script setup>
const logo = import.meta.env.BASE_URL + 'icon.svg'
const features = [
  ['🖼️', 'Online exhibitions', 'Curate your batch shows with a shareable public page, before, during and after the physical show.'],
  ['🏷️', 'Sell artworks', 'Collectors send purchase requests; the artist accepts and arranges payment directly.'],
  ['🔨', 'Live auctions', 'Run timed auctions with minimum increments, a hidden reserve and anti-sniping.'],
  ['💬', 'Batch chat', 'A group chat for the whole batch plus direct messages with buyers.'],
]
</script>

<template>
  <div class="page no-nav">
    <header class="row between" style="padding: .4rem 0 1.2rem">
      <div class="brand"><img :src="logo" alt="" />Chayabari</div>
      <RouterLink to="/login" class="btn sm ghost">Log in</RouterLink>
    </header>

    <section class="hero-block">
      <span class="badge accent">For fine art student batches</span>
      <h1 class="display">Your batch's gallery, shop and auction house — in your pocket.</h1>
      <p class="muted">One student subscribes for the whole batch, adds classmates, and everyone starts showing and selling their work.</p>
      <div class="stack">
        <RouterLink to="/signup" class="btn accent block">Start a free trial for your batch</RouterLink>
        <RouterLink to="/explore" class="btn ghost block">Browse artworks</RouterLink>
      </div>
    </section>

    <section class="section stack">
      <div v-for="[icon, title, text] in features" :key="title" class="card row" style="align-items: flex-start">
        <div style="font-size: 1.6rem">{{ icon }}</div>
        <div><h3>{{ title }}</h3><p class="small muted" style="margin: 0">{{ text }}</p></div>
      </div>
    </section>

    <section class="section card">
      <h2>How it works</h2>
      <ol class="muted steps">
        <li>One student creates the batch account (14-day free trial).</li>
        <li>They add their classmates — Chayabari generates usernames and passwords.</li>
        <li>Share each login privately. Everyone sets their own password on first login.</li>
        <li>Upload artworks, open an exhibition, start selling. Pay by bKash/Nagad when ready.</li>
      </ol>
    </section>

    <p class="center small muted section">
      Want to buy art? <RouterLink to="/register"><b>Create a collector account</b></RouterLink>
    </p>
  </div>
</template>

<style scoped>
.hero-block { padding: 1rem 0; }
.display { font-size: 2.1rem; margin: .8rem 0; }
.steps { padding-left: 1.2rem; margin: 0; } .steps li { margin-bottom: .4rem; }
</style>
