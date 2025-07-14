import { mount } from 'svelte'
import './app.css'
import App from './App.svelte'

const urlParams = new URLSearchParams(window.location.search);
const namespaceId = urlParams.get('namespace_id');

const app = mount(App, {
  target: document.getElementById('app'),
  props: {
    namespaceId
  }
})

export default app
