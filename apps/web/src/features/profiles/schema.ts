import { z } from "zod";
import type { ProfileUpdate } from "@/lib/api/types";

export const BRANCHES = [
  "Computer Science and Engineering",
  "Artificial Intelligence and Data Science",
  "Mathematics and Computing",
  "Other",
] as const;

export const YEARS = [
  { value: "1", label: "1st year" },
  { value: "2", label: "2nd year" },
  { value: "3", label: "3rd year" },
  { value: "4", label: "4th year" },
  { value: "5", label: "5th year or later" },
] as const;

export const BIO_MAX = 500;

// Mirrors the API's validation (apps/api/app/modules/profiles/schemas.py). The API is the
// source of truth; this exists to give instant feedback.
export const profileFormSchema = z.object({
  name: z.string().trim().min(1, "Enter your name").max(100, "Keep your name under 100 characters"),
  branch: z.string().min(1, "Choose your branch"),
  year: z.string().regex(/^[1-5]$/, "Choose your year"),
  bio: z.string().max(BIO_MAX, `Keep your bio under ${BIO_MAX} characters`),
});

export type ProfileFormValues = z.infer<typeof profileFormSchema>;

export function toPayload(values: ProfileFormValues): ProfileUpdate {
  return {
    name: values.name.trim(),
    branch: values.branch,
    year: Number(values.year),
    bio: values.bio.trim() === "" ? null : values.bio,
  };
}
