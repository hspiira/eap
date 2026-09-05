import { useEffect, useState } from "react"

import * as SelectPrimitive from "@radix-ui/react-select"
import { useQuery } from "@tanstack/react-query"
import { Check, ChevronsUpDown } from "lucide-react"
import { Controller, useWatch } from "react-hook-form"
import { z } from "zod"

import { clientsApi } from "@/api/endpoints/clients"
import { contactsApi } from "@/api/endpoints/contacts"
import { industriesApi } from "@/api/endpoints/industries"
import type { ClientCreate, ClientUpdate } from "@/api/generated"
import { FormField } from "@/components/common/FormField"
import { FormSection } from "@/components/common/FormSection"
import { SheetForm } from "@/components/common/SheetForm"
import { Button } from "@/components/ui/button"
import { Checkbox } from "@/components/ui/checkbox"
import { Collapsible, CollapsibleContent } from "@/components/ui/collapsible"
import {
  Command,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
} from "@/components/ui/command"
import { Input } from "@/components/ui/input"
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { useEntityFormSheet } from "@/hooks/useEntityFormSheet"
import { cn } from "@/lib/utils"
import type { Client } from "@/types/entities"
import { ClientTier, ContactMethod } from "@/types/enums"

const TIER_OPTIONS = [
  { value: ClientTier.A, label: "Tier A", desc: "Strategic: full service mix" },
  { value: ClientTier.B, label: "Tier B", desc: "Mid-tier: consultancy extension" },
  { value: ClientTier.C, label: "Tier C", desc: "Long-tail: lower-touch model" },
] as const

const TIER_VALUES = TIER_OPTIONS.map((o) => o.value) as [ClientTier, ...ClientTier[]]

const CONTACT_METHOD_OPTIONS = [
  { value: ContactMethod.EMAIL, label: "Email" },
  { value: ContactMethod.PHONE, label: "Phone" },
  { value: ContactMethod.SMS, label: "SMS" },
  { value: ContactMethod.WHATSAPP, label: "WhatsApp" },
  { value: ContactMethod.WECHAT, label: "WeChat" },
] as const

const clientSchema = z
  .object({
    name: z.string().trim().min(1, "Name is required"),
    code: z
      .string()
      .trim()
      .min(3, "Code must be 3–5 characters")
      .max(5, "Code must be 3–5 characters")
      .regex(/^[A-Za-z0-9]+$/, "Code must use letters and numbers only"),
    tier: z.enum(["", ...TIER_VALUES] as readonly [string, ...string[]]).optional(),
    billing_address_different: z.boolean(),
    preferred_contact_method: z
      .enum(["", ...CONTACT_METHOD_OPTIONS.map((o) => o.value)] as readonly [string, ...string[]])
      .optional(),
    contact_person_name: z.string().trim().optional(),
    email: z
      .string()
      .trim()
      .optional()
      .refine((v) => !v || /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(v), "Invalid email"),
    phone: z.string().optional(),
    address: z.string().optional(),
    billing_street: z.string().optional(),
    billing_city: z.string().optional(),
    billing_postal: z.string().optional(),
    billing_country: z.string().optional(),
    industry_id: z.string().optional(),
  })
  .superRefine((d, ctx) => {
    if (!d.billing_address_different) return
    for (const f of ["billing_street", "billing_city", "billing_country"] as const) {
      if (!d[f]?.trim()) {
        ctx.addIssue({
          code: "custom",
          path: [f],
          message: "Required when any billing field is set",
        })
      }
    }
  })

type ClientFormValues = z.infer<typeof clientSchema>

const EMPTY: ClientFormValues = {
  name: "",
  code: "",
  tier: "",
  billing_address_different: false,
  preferred_contact_method: "",
  contact_person_name: "",
  email: "",
  phone: "",
  address: "",
  billing_street: "",
  billing_city: "",
  billing_postal: "",
  billing_country: "",
  industry_id: "",
}

interface ClientFormSheetProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  client?: Client | null
  onSaved?: (client: Client) => void
}

export function ClientFormSheet({ open, onOpenChange, client, onSaved }: ClientFormSheetProps) {
  const [industryOpen, setIndustryOpen] = useState(false)

  const { data: industriesPage } = useQuery({
    queryKey: ["industries", "picker"],
    queryFn: () => industriesApi.list({ limit: 200 }),
    enabled: open,
    staleTime: 5 * 60 * 1000,
  })
  const industryOptions = industriesPage?.items ?? []

  const { register, control, formState, submit, serverError, isEdit, setValue } =
    useEntityFormSheet<
      ClientFormValues,
      ClientCreate & { __tier?: ClientTier | null },
      Client,
      Client
    >({
      resource: "clients",
      schema: clientSchema,
      defaultValues: EMPTY,
      open,
      onOpenChange,
      entity: client,
      toFormValues: (c) => ({
        name: c.name,
        code: c.code,
        tier: c.tier ?? "",
        billing_address_different: !!c.billing_address,
        preferred_contact_method: c.preferred_contact_method ?? "",
        contact_person_name: "",
        email: c.contact_info?.email ?? "",
        phone: c.contact_info?.phone ?? "",
        address: c.contact_info?.address ?? "",
        billing_street: c.billing_address?.street ?? "",
        billing_city: c.billing_address?.city ?? "",
        billing_postal: c.billing_address?.postal_code ?? "",
        billing_country: c.billing_address?.country ?? "",
        industry_id: c.industry_id ?? "",
      }),
      parsePayload: (values) => ({
        name: values.name,
        code: values.code,
        contact_info: {
          email: values.email || null,
          phone: values.phone || null,
          address: values.address || null,
        },
        contact_person_name: values.contact_person_name || null,
        billing_address:
          values.billing_address_different &&
          values.billing_street &&
          values.billing_city &&
          values.billing_country
            ? {
                street: values.billing_street,
                city: values.billing_city,
                country: values.billing_country,
                postal_code: values.billing_postal || null,
              }
            : null,
        industry_id: values.industry_id || null,
        preferred_contact_method: values.preferred_contact_method
          ? (values.preferred_contact_method as ContactMethod)
          : null,
        __tier: values.tier ? (values.tier as ClientTier) : null,
      }),
      save: async ({ payload, entity, isEdit }) => {
        const { __tier, ...createPayload } = payload
        let saved: Client
        if (isEdit && entity) {
          const update: ClientUpdate = {
            name: createPayload.name,
            contact_info: createPayload.contact_info,
            contact_person_name: createPayload.contact_person_name,
            billing_address: createPayload.billing_address,
            industry_id: createPayload.industry_id,
            preferred_contact_method: createPayload.preferred_contact_method,
            tier: __tier,
          }
          saved = await clientsApi.update(entity.id, update)
        } else {
          saved = await clientsApi.create(createPayload)
          if (__tier) {
            saved = await clientsApi.setTier(saved.id, __tier)
          }
        }
        return saved
      },
      successToast: { create: "Client created", update: "Client updated" },
      onSaved,
    })

  const contactsQuery = useQuery({
    queryKey: ["contacts", "client", client?.id],
    queryFn: () => contactsApi.byClient(client!.id),
    enabled: open && isEdit && Boolean(client?.id),
  })

  const primaryContactName = contactsQuery.data?.find((contact) => contact.is_primary)?.name ?? ""

  useEffect(() => {
    if (open && isEdit && contactsQuery.isSuccess) {
      setValue("contact_person_name", primaryContactName)
    }
  }, [contactsQuery.isSuccess, isEdit, open, primaryContactName, setValue])

  const billingAddressDifferent = useWatch({ control, name: "billing_address_different" })

  const errors = formState.errors

  return (
    <SheetForm
      open={open}
      onOpenChange={onOpenChange}
      title={isEdit ? "Edit client" : "Add client"}
      description={
        isEdit
          ? "Update identity, tiering, and contact details."
          : "Create a new corporate client. You can link contracts, services, and staff after saving."
      }
      size="md"
      onSubmit={submit}
      isSubmitting={formState.isSubmitting}
      serverError={serverError}
      submitLabel={isEdit ? "Save changes" : "Create client"}
      submittingLabel={isEdit ? "Saving…" : "Creating…"}
    >
      <p className="text-xs text-fg-muted">Fields marked * are required.</p>
      <FormSection title="Identity">
        <FormField label="Name" required error={errors.name?.message} htmlFor="cs-name">
          <Input id="cs-name" placeholder="e.g. Acme Corp" {...register("name")} />
        </FormField>
        <FormField
          label="Code"
          description="3–5 character code used in employee references."
          required
          error={errors.code?.message}
          htmlFor="cs-code"
        >
          <Input
            id="cs-code"
            placeholder="ACME"
            maxLength={5}

            disabled={isEdit}
            {...register("code")}
          />
        </FormField>
      </FormSection>

      <FormSection title="Tiering & sector">
        <FormField label="Tier" error={errors.tier?.message} htmlFor="cs-tier">
          <Controller
            control={control}
            name="tier"
            render={({ field }) => (
              <Select value={field.value ?? ""} onValueChange={field.onChange}>
                <SelectTrigger id="cs-tier">
                  <SelectValue placeholder="Unassigned" />
                </SelectTrigger>
                <SelectContent>
                  {TIER_OPTIONS.map(({ value, label, desc }) => (
                    <SelectPrimitive.Item
                      key={value}
                      value={value}
                      className="relative flex w-full cursor-default select-none rounded-sm py-2 pl-2 pr-8 text-sm outline-none focus:bg-accent focus:text-accent-foreground data-disabled:pointer-events-none data-disabled:opacity-50"
                    >
                      <span className="absolute right-2 flex h-3.5 w-3.5 items-center justify-center mt-0.5">
                        <SelectPrimitive.ItemIndicator>
                          <Check className="h-4 w-4" />
                        </SelectPrimitive.ItemIndicator>
                      </span>
                      <div className="flex flex-col">
                        <SelectPrimitive.ItemText>{label}</SelectPrimitive.ItemText>
                        <span className="text-xs text-muted-foreground leading-tight mt-0.5">
                          {desc}
                        </span>
                      </div>
                    </SelectPrimitive.Item>
                  ))}
                </SelectContent>
              </Select>
            )}
          />
        </FormField>

        <FormField
          label="Industry"
          description={
            isEdit
              ? "Use the industry classification for benchmarking and reporting."
              : "The sector this client operates in. Drives benchmarking and reporting."
          }
          error={errors.industry_id?.message}
          htmlFor="cs-industry"
        >
          <Controller
            control={control}
            name="industry_id"
            render={({ field }) => (
              <Popover open={industryOpen} onOpenChange={setIndustryOpen}>
                <PopoverTrigger asChild>
                  <Button
                    id="cs-industry"
                    type="button"
                    variant="outline"
                    role="combobox"
                    aria-expanded={industryOpen}
                    className={cn(
                      "w-full h-9 justify-between px-3 font-normal text-sm",
                      !field.value && "text-muted-foreground",
                    )}
                  >
                    <span className="truncate">
                      {field.value
                        ? (industryOptions.find((i) => i.id === field.value)?.name ?? "No industry")
                        : "No industry"}
                    </span>
                    <ChevronsUpDown className="ml-2 h-4 w-4 shrink-0 opacity-50" />
                  </Button>
                </PopoverTrigger>
                <PopoverContent
                  className="p-0"
                  align="start"
                  style={{ width: "var(--radix-popover-trigger-width)" }}
                >
                  <Command>
                    <CommandInput placeholder="Search industries…" />
                    <CommandList>
                      <CommandEmpty>No industries found.</CommandEmpty>
                      <CommandGroup>
                        <CommandItem
                          value="__none"
                          onSelect={() => {
                            field.onChange("")
                            setIndustryOpen(false)
                          }}
                        >
                          <Check
                            className={cn(
                              "mr-2 h-4 w-4",
                              !field.value ? "opacity-100" : "opacity-0",
                            )}
                          />
                          No industry
                        </CommandItem>
                        {industryOptions.map((ind) => (
                          <CommandItem
                            key={ind.id}
                            value={ind.name}
                            onSelect={() => {
                              field.onChange(ind.id)
                              setIndustryOpen(false)
                            }}
                          >
                            <Check
                              className={cn(
                                "mr-2 h-4 w-4",
                                field.value === ind.id ? "opacity-100" : "opacity-0",
                              )}
                            />
                            {ind.name}
                          </CommandItem>
                        ))}
                      </CommandGroup>
                    </CommandList>
                  </Command>
                </PopoverContent>
              </Popover>
            )}
          />
        </FormField>
      </FormSection>

      <FormSection
        title="Contact details"
        description="Add the organisation’s contact details and, when creating a client, the contact person’s name."
      >
        <FormField
          label="Contact person name"
          error={errors.contact_person_name?.message}
          htmlFor="cs-contact-person-name"
        >
          <Input
            id="cs-contact-person-name"
            placeholder="e.g. Doreen Muwulya"
            {...register("contact_person_name")}
          />
        </FormField>
        <FormField label="Email" error={errors.email?.message} htmlFor="cs-email">
          <Input id="cs-email" type="email" placeholder="contact@acme.com" {...register("email")} />
        </FormField>
        <FormField
          label="Preferred contact method"
          error={errors.preferred_contact_method?.message}
          htmlFor="cs-preferred-contact"
        >
          <Controller
            control={control}
            name="preferred_contact_method"
            render={({ field }) => (
              <Select value={field.value ?? ""} onValueChange={field.onChange}>
                <SelectTrigger id="cs-preferred-contact">
                  <SelectValue placeholder="No preference" />
                </SelectTrigger>
                <SelectContent>
                  {CONTACT_METHOD_OPTIONS.map((option) => (
                    <SelectItem key={option.value} value={option.value}>
                      {option.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            )}
          />
        </FormField>
        <FormField label="Phone" error={errors.phone?.message} htmlFor="cs-phone">
          <Input id="cs-phone" type="tel" placeholder="+256 …" {...register("phone")} />
        </FormField>
        <FormField label="Address" error={errors.address?.message} htmlFor="cs-address">
          <Input id="cs-address" placeholder="Street, city" {...register("address")} />
        </FormField>
      </FormSection>

      <FormSection
        title="Billing address"
        description="By default, invoices use the contact address."
      >
        <div className="flex items-start gap-2">
          <Controller
            control={control}
            name="billing_address_different"
            render={({ field }) => (
              <Checkbox
                id="cs-billing-different"
                checked={field.value}
                onCheckedChange={(checked) => field.onChange(checked === true)}
              />
            )}
          />
          <div className="grid gap-0.5">
            <label htmlFor="cs-billing-different" className="text-sm text-fg">
              Billing address is different
            </label>
            <p className="text-xs text-fg-muted">Add a separate address for invoices.</p>
          </div>
        </div>
        <Collapsible open={billingAddressDifferent}>
          <CollapsibleContent className="space-y-3.5 pt-3">
            <FormField
              label="Street"
              required={billingAddressDifferent}
              error={errors.billing_street?.message}
              htmlFor="cs-billing-street"
            >
              <Input id="cs-billing-street" {...register("billing_street")} />
            </FormField>
            <div className="grid grid-cols-2 gap-3">
              <FormField
                label="City"
                required={billingAddressDifferent}
                error={errors.billing_city?.message}
                htmlFor="cs-billing-city"
              >
                <Input id="cs-billing-city" {...register("billing_city")} />
              </FormField>
              <FormField
                label="Postal code"
                error={errors.billing_postal?.message}
                htmlFor="cs-billing-postal"
              >
                <Input id="cs-billing-postal" {...register("billing_postal")} />
              </FormField>
            </div>
            <FormField
              label="Country"
              required={billingAddressDifferent}
              error={errors.billing_country?.message}
              htmlFor="cs-billing-country"
            >
              <Input
                id="cs-billing-country"
                placeholder="Uganda"
                {...register("billing_country")}
              />
            </FormField>
          </CollapsibleContent>
        </Collapsible>
      </FormSection>
    </SheetForm>
  )
}
