<script>
  import '../app.css';

  let { children } = $props();

  import { Navbar, NavBrand, NavLi, NavUl, NavHamburger } from "flowbite-svelte";
</script>

<Navbar>
  <NavBrand href="/">
    <!--<img src="/images/flowbite-svelte-icon-logo.svg" class="me-3 h-6 sm:h-9" alt="Flowbite Logo" />-->
    <span class="self-center text-xl font-semibold whitespace-nowrap dark:text-white">Biota Taiwanica</span>
  </NavBrand>
  <NavHamburger />
  <NavUl>
    <NavLi href="/">Home</NavLi>
    <NavLi href="/login">login</NavLi>
  </NavUl>
</Navbar>

<div class="container mx-auto px-4 py-8">
  {@render children()}
</div>
