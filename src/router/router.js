import { createRouter, createWebHistory } from 'vue-router';
import store from '@/store/store.js';
import Error404 from '@/views/GeneralError404.vue';
import usersRoutes from '@/router/users.js';
import todosRoutes from '@/router/todos.js';
import goalsRoutes from '@/router/goals.js';
import notesRoutes from '@/router/notes.js';

// Dispatch autoLogin action
store.dispatch('autoLogin');

const routes = [
  {
    path: '/',
    meta: {
      requiresAuthenticationTrue: false,
      forceRedirect: true,
    },
  },
  ...todosRoutes,
  ...usersRoutes,
  ...goalsRoutes,
  ...notesRoutes,
  {
    path: '/:pathMatch(.*)*',
    component: Error404,
  },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

router.beforeEach((to, from, next) => {
  if (to.matched.some((record) => record.meta.requiresAuthenticationTrue)) {
    if (!store.getters.isAuthenticated) {
      next({
        path: '/signin/',
        query: { redirect: to.fullPath },
      });
    }
  }
  if (to.matched.some((record) => record.meta.requiresAuthenticationFalse)) {
    if (store.getters.isAuthenticated) {
      next({
        path: '/t/dashboard/',
      });
    }
  }
  if (to.matched.some((record) => record.meta.forceRedirect)) {
    if (store.getters.isAuthenticated) {
      next({
        path: '/t/dashboard/',
      });
    } else {
      next({
        path: '/signin/',
      });
    }
  }
  next();
});

export default router;