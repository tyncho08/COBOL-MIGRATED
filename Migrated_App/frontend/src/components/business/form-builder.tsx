'use client'

import { useForm, FieldValues, DefaultValues } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Select, SelectOption } from '@/components/ui/select'
import { Card, CardContent, CardFooter } from '@/components/ui/card'

export interface FormField {
  name: string
  label: string
  type: 'text' | 'email' | 'number' | 'date' | 'select' | 'textarea'
  required?: boolean
  placeholder?: string
  options?: SelectOption[]
  defaultValue?: any
  validation?: z.ZodTypeAny
}

interface FormBuilderProps<T extends FieldValues> {
  fields: FormField[]
  onSubmit: (data: T) => void
  defaultValues?: DefaultValues<T>
  submitLabel?: string
  cancelLabel?: string
  onCancel?: () => void
  loading?: boolean
  schema?: z.ZodSchema<T>
}

export function FormBuilder<T extends FieldValues>({
  fields,
  onSubmit,
  defaultValues,
  submitLabel = 'Submit',
  cancelLabel = 'Cancel',
  onCancel,
  loading = false,
  schema
}: FormBuilderProps<T>) {
  const {
    register,
    handleSubmit,
    formState: { errors },
    reset
  } = useForm<T>({
    resolver: schema ? zodResolver(schema) : undefined,
    defaultValues
  })

  const renderField = (field: FormField) => {
    const error = errors[field.name]?.message as string

    switch (field.type) {
      case 'select':
        return (
          <Select
            key={field.name}
            label={field.label}
            required={field.required}
            error={error}
            options={field.options || []}
            placeholder={field.placeholder}
            {...register(field.name as any)}
          />
        )
      
      case 'textarea':
        return (
          <div key={field.name} className="w-full">
            <label className="block text-sm font-medium text-gray-700 mb-1">
              {field.label}
              {field.required && <span className="text-red-500 ml-1">*</span>}
            </label>
            <textarea
              className="block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
              rows={3}
              placeholder={field.placeholder}
              {...register(field.name as any)}
            />
            {error && (
              <p className="mt-1 text-sm text-red-600">{error}</p>
            )}
          </div>
        )

      default:
        return (
          <Input
            key={field.name}
            label={field.label}
            type={field.type}
            required={field.required}
            placeholder={field.placeholder}
            error={error}
            {...register(field.name as any)}
          />
        )
    }
  }

  return (
    <Card>
      <form onSubmit={handleSubmit(onSubmit)}>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            {fields.map(renderField)}
          </div>
        </CardContent>
        
        <CardFooter className="flex space-x-2">
          <Button type="submit" loading={loading}>
            {submitLabel}
          </Button>
          {onCancel && (
            <Button type="button" variant="outline" onClick={onCancel}>
              {cancelLabel}
            </Button>
          )}
        </CardFooter>
      </form>
    </Card>
  )
}