import type { PageServerLoad, Actions } from "./$types.js";
import { fail } from "@sveltejs/kit";
import { superValidate } from "sveltekit-superforms";
import { zod } from "sveltekit-superforms/adapters";
import { formSchema } from "./schema";
import { supabase } from "$lib/auth/supabase";
 
export const load: PageServerLoad = async () => {
  const form = await superValidate(zod(formSchema));
  
  // Ensure default values are set
  form.data = {
    is_hosted: false,
    agent_url: "",
    launcher_url: "",
    docker_image_link: "",
    alias: "",
    green: false,
    battle_description: "",
    participant_requirements: [],
    battle_timeout: 300
  };
  
  return {
    form,
  };
};