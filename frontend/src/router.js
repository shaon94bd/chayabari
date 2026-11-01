import { createRouter, createWebHistory } from 'vue-router'
import { useAuth } from './stores/auth'

const v = (name) => () => import(`./views/${name}.vue`)

// meta.auth: must be logged in · meta.student: batch member · meta.owner: batch owner
// meta.nav: show the bottom navigation
const routes = [
  { path: '/', component: v('Landing'), meta: { guestOnly: true } },
  { path: '/login', component: v('Login'), meta: { guestOnly: true } },
  { path: '/signup', component: v('Signup'), meta: { guestOnly: true } },
  { path: '/register', component: v('Register'), meta: { guestOnly: true } },
  { path: '/change-password', component: v('ChangePassword'), meta: { auth: true } },

  { path: '/home', component: v('Home'), meta: { auth: true, nav: true } },
  { path: '/explore', component: v('Explore'), meta: { nav: true } },
  { path: '/artworks/new', component: v('ArtworkForm'), meta: { student: true } },
  { path: '/artworks/:id', component: v('ArtworkDetail'), meta: { nav: true } },
  { path: '/artworks/:id/edit', component: v('ArtworkForm'), meta: { student: true } },

  { path: '/exhibitions', component: v('Exhibitions'), meta: { nav: true } },
  { path: '/exhibitions/new', component: v('ExhibitionForm'), meta: { student: true } },
  { path: '/exhibitions/:id', component: v('ExhibitionDetail'), meta: { nav: true } },
  { path: '/exhibitions/:id/edit', component: v('ExhibitionForm'), meta: { student: true } },

  { path: '/auctions', component: v('Auctions'), meta: { nav: true } },
  { path: '/auctions/new', component: v('AuctionForm'), meta: { student: true } },
  { path: '/auctions/:id', component: v('AuctionDetail'), meta: { nav: true } },

  { path: '/chat', component: v('Inbox'), meta: { auth: true, nav: true } },
  { path: '/chat/:id', component: v('ChatThread'), meta: { auth: true } },

  { path: '/me', component: v('Me'), meta: { auth: true, nav: true } },
  { path: '/me/edit', component: v('EditProfile'), meta: { auth: true } },
  { path: '/orders', component: v('Orders'), meta: { auth: true, nav: true } },

  { path: '/group/members', component: v('BatchMembers'), meta: { student: true } },
  { path: '/group/billing', component: v('Billing'), meta: { student: true } },
  { path: '/group/settings', component: v('BatchSettings'), meta: { owner: true } },
  { path: '/batch/:page(members|billing|settings)', redirect: (to) => `/group/${to.params.page}` },

  { path: '/b/:slug', component: v('PublicBatch'), meta: { nav: true } },
  { path: '/artists/:username', component: v('ArtistProfile'), meta: { nav: true } },
  { path: '/:pathMatch(.*)*', component: v('NotFound') },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior: (to, from, saved) => saved || { top: 0 },
})

router.beforeEach((to) => {
  const auth = useAuth()
  const needsLogin = to.meta.auth || to.meta.student || to.meta.owner
  if (needsLogin && !auth.loggedIn) return { path: '/login', query: { next: to.fullPath } }
  if (auth.loggedIn && auth.user.must_change_password && to.path !== '/change-password') return '/change-password'
  if (to.meta.guestOnly && auth.loggedIn) return '/home'
  if (to.meta.student && !auth.isStudent) return '/home'
  if (to.meta.owner && !auth.isOwner) return '/home'
})

export default router
