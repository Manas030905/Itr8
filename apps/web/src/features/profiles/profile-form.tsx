"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useForm, useWatch } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { Button } from "@/components/ui/button";
import { FieldError, Input, Label, Select, Textarea } from "@/components/ui/field";
import { api } from "@/lib/api/browser";
import { BIO_MAX, BRANCHES, YEARS, profileFormSchema, toPayload, type ProfileFormValues } from "./schema";

export function ProfileForm({ initial }: { initial: ProfileFormValues }) {
  const router = useRouter();
  const [formError, setFormError] = useState<string | null>(null);
  const {
    register,
    handleSubmit,
    control,
    formState: { errors, isSubmitting },
  } = useForm<ProfileFormValues>({ resolver: zodResolver(profileFormSchema), defaultValues: initial });

  const bioLength = useWatch({ control, name: "bio" })?.length ?? 0;

  async function onSubmit(values: ProfileFormValues) {
    setFormError(null);
    try {
      const { response } = await api.PATCH("/api/v1/profiles/me", { body: toPayload(values) });
      if (response.status === 401) {
        router.push("/login");
        return;
      }
      if (!response.ok) {
        setFormError(
          response.status === 422
            ? "Some details weren't accepted. Check the fields and try again."
            : "We couldn't save your profile. Please try again.",
        );
        return;
      }
      router.push("/me");
      router.refresh();
    } catch {
      setFormError("Couldn't reach the server. Check your connection and try again.");
    }
  }

  return (
    <form onSubmit={handleSubmit(onSubmit)} noValidate className="space-y-5">
      {formError && (
        <p role="alert" className="rounded-lg bg-danger-soft px-4 py-3 text-sm text-danger">
          {formError}
        </p>
      )}

      <div>
        <Label htmlFor="name">Name</Label>
        <Input id="name" autoComplete="name" aria-invalid={!!errors.name} aria-describedby="name-error" {...register("name")} />
        <FieldError id="name-error">{errors.name?.message}</FieldError>
      </div>

      <div className="grid gap-5 sm:grid-cols-2">
        <div>
          <Label htmlFor="branch">Branch</Label>
          <Select id="branch" aria-invalid={!!errors.branch} aria-describedby="branch-error" {...register("branch")}>
            <option value="">Choose your branch</option>
            {BRANCHES.map((b) => (
              <option key={b} value={b}>{b}</option>
            ))}
          </Select>
          <FieldError id="branch-error">{errors.branch?.message}</FieldError>
        </div>
        <div>
          <Label htmlFor="year">Year</Label>
          <Select id="year" aria-invalid={!!errors.year} aria-describedby="year-error" {...register("year")}>
            <option value="">Choose your year</option>
            {YEARS.map((y) => (
              <option key={y.value} value={y.value}>{y.label}</option>
            ))}
          </Select>
          <FieldError id="year-error">{errors.year?.message}</FieldError>
        </div>
      </div>

      <div>
        <div className="flex items-baseline justify-between">
          <Label htmlFor="bio">Short bio (optional)</Label>
          <span className={bioLength > BIO_MAX ? "text-sm text-danger" : "text-sm text-slate"}>
            {bioLength}/{BIO_MAX}
          </span>
        </div>
        <Textarea id="bio" placeholder="What do you like building? What are you learning right now?" aria-invalid={!!errors.bio} aria-describedby="bio-error" {...register("bio")} />
        <FieldError id="bio-error">{errors.bio?.message}</FieldError>
      </div>

      <Button type="submit" size="lg" disabled={isSubmitting}>
        {isSubmitting ? "Saving…" : "Save profile"}
      </Button>
    </form>
  );
}
