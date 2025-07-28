import { d as derived } from "./index2.js";
import { u as user } from "./supabase.js";
derived(user, ($user) => !!$user);
derived(user, ($user) => $user?.email);
derived(user, ($user) => $user?.user_metadata?.name || $user?.email);
derived(user, ($user) => $user?.id);
