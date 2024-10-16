import { createApp } from "vue";
import App from "./App.vue";
import router from "@/router/router.js";
import store from "@/store/store.js";
// import VueFormulate from "@braid/vue-formulate";
import "@/assets/global.css";
import { plugin, defaultConfig } from "@formkit/vue";

// Vue.use(VueFormulate);

// vue
const app = createApp(App);

// Vue.config.productionTip = false;

// formkit
app.use(plugin, defaultConfig);

// Vue.use(VueFormulate, {
//   classes: {
//     outer: "mb-4 last:mb-0",
//     input(context) {
//       switch (context.classification) {
//         case "button":
//           return "ml-auto cursor-pointer flex flex-row items-center px-6 py-2 tracking-wide font-bold rounded-lg text-gray-200 hover:bg-blue-900 bg-blue-800 shadow transition duration-100 ease-in-out focus:outline-none focus:shadow-outline";
//         case "box":
//           return "border-gray-400 rounded leading-none focus:border-blue-700 border-2 outline-none border-box w-4 h-4 align-text-top mr-1";
//         default:
//           return "border-gray-400 rounded px-3 py-2 leading-none focus:border-blue-700 border-2 outline-none border-box mb-1 w-full";
//       }
//     },
//     label: "font-medium text-sm",
//     help: "text-xs mb-1 text-gray-600",
//     error: "text-red-700 text-xs mb-1",
//   },
//   errorHandler: function(data) {
//     return {
//       inputErrors: data,
//       formErrors: data.non_field_errors,
//     };
//   },
// });


// vuex store
app.use(store);
app.mixin({
  computed: {
    alert() {
      return this.$store.state.alert;
    },
  },
  watch: {
    $route() {
      // clear alert on location change
      this.$store.dispatch('alert/clear');
    },
  },
});

// router
app.use(router);

// mount
app.mount("#app");

store.$app = app;
