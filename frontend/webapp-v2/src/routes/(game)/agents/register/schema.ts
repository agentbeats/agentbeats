import { z } from "zod";
 
export const formSchema = z.object({
  agent_url: z.string().min(1, "Agent URL is required"),
  launcher_url: z.string().min(1, "Launcher URL is required"),
  alias: z.string().optional().default(""),
  green: z.boolean().default(false),
  participant_requirements: z.array(z.object({
    id: z.number().optional(),
    role: z.string().default(""),
    name: z.string().default(""),
    required: z.boolean().default(false)
  })).default([]),
  task_config: z.string().optional().default(""),
  battle_timeout: z.number().min(1).default(300)
});
 
export type FormSchema = typeof formSchema;