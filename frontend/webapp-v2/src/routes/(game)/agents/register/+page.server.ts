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
    agent_url: "",
    launcher_url: "",
    alias: "",
    green: false,
    participant_requirements: [],
    task_config: "",
    battle_timeout: 300
  };  
  
  return {
    form,
  };
};
 
export const actions: Actions = {
  default: async (event) => {
    console.log('Server action triggered');
    const form = await superValidate(event, zod(formSchema));
    console.log('Form validation result:', { valid: form.valid, data: form.data });
    
    if (!form.valid) {
      console.log('Form validation failed:', form.errors);
      return fail(400, {
        form,
      });
    }

    try {
      // Check if we're in dev_login mode
      const isDevMode = process.env.VITE_DEV_LOGIN === "true";
      let accessToken: string | null = null;
      
      if (isDevMode) {
        // In dev mode, use mock access token
        accessToken = 'dev-access-token';
        console.log('Dev mode enabled, using mock access token');
      } else {
        // Production mode: Get the session from the request cookies
        const sessionCookie = event.cookies.get('agentbeats-auth');
        console.log('Session cookie found:', !!sessionCookie);
        console.log('Available cookies:', Array.from(event.cookies.getAll()).map(c => c.name));
        
        if (!sessionCookie) {
          return fail(401, {
            form,
            error: 'No session found'
          });
        }

        // Parse the session data to get the access token
        try {
          const sessionData = JSON.parse(sessionCookie);
          accessToken = sessionData.access_token;
          console.log('Access token extracted:', !!accessToken);
        } catch (error) {
          console.error('Failed to parse session data:', error);
          return fail(401, {
            form,
            error: 'Invalid session data'
          });
        }

        if (!accessToken) {
          return fail(401, {
            form,
            error: 'No access token found in session'
          });
        }
      }

      const requestBody = {
        agent_url: form.data.agent_url,
        launcher_url: form.data.launcher_url,
        alias: form.data.alias,
        is_green: form.data.green,
        participant_requirements: form.data.participant_requirements,
        battle_timeout: form.data.battle_timeout,
        task_config: form.data.task_config
      };
      
      console.log('Form data alias:', form.data.alias);
      console.log('Request body alias:', requestBody.alias);
      console.log('Sending request to backend:', requestBody);
      
      const response = await fetch('http://localhost:9000/agents', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${accessToken}`
        },
        body: JSON.stringify(requestBody)
      });

      if (!response.ok) {
        const errorData = await response.json();
        return fail(response.status, {
          form,
          error: errorData.detail || 'Failed to register agent'
        });
      }

      const result = await response.json();
      return {
        form,
        success: true,
        data: result
      };
    } catch (error) {
      return fail(500, {
        form,
        error: 'Network error: Failed to connect to backend'
      });
    }
  },
};