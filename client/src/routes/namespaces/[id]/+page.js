import { PUBLIC_BACKEND_URL } from '$env/static/public';

/** @type {import('./$types').PageLoad} */
export async function load({ fetch, params }) {
  const res = await fetch(`${PUBLIC_BACKEND_URL}/api/namespaces/${params.id}`);
  const data = await res.json();
  return { data };
}
