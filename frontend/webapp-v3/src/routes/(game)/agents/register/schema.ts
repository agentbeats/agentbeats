import { z } from "zod";
 
export const formSchema = z.object({
  is_hosted: z.boolean().default(false),
  agent_url: z.string().optional().default(""),
  launcher_url: z.string().optional().default(""),
  docker_image_link: z.string().optional().default(""),
  alias: z.string().min(1, "Agent alias is required"),
  green: z.boolean().default(false),
  battle_description: z.string().optional().default(""),
  participant_requirements: z.array(z.object({
    id: z.number().optional(),
    role: z.string().default(""),
    name: z.string().default(""),
    required: z.boolean().default(false)
  })).default([]),
  battle_timeout: z.number().min(1).default(300)
}).superRefine((data, ctx) => {
  // Validation logic based on agent type
  if (data.is_hosted) {
    // Hosted agent: docker_image_link is required
    if (!data.docker_image_link || data.docker_image_link.trim() === "") {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        message: "GitHub link is required for hosted agents",
        path: ["docker_image_link"]
      });
    }
  } else {
    // Remote agent: agent_url and launcher_url are required
    if (!data.agent_url || data.agent_url.trim() === "") {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        message: "Agent URL is required for remote agents",
        path: ["agent_url"]
      });
    }
    if (!data.launcher_url || data.launcher_url.trim() === "") {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        message: "Launcher URL is required for remote agents",
        path: ["launcher_url"]
      });
    }
  }
});
 
export type FormSchema = typeof formSchema;