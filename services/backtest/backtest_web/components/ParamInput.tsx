"use client"

import { useState, useEffect } from "react"
import { backtestApi } from "@/lib/backtest-api"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { AlertCircle, CheckCircle } from "lucide-react"

interface ParamInputProps {
  strategyId: string
  paramName: string
  paramValue: any
  onChange: (name: string, value: any) => void
  label?: string
  type?: "number" | "text"
  min?: number
  max?: number
}

export function ParamInput({
  strategyId,
  paramName,
  paramValue,
  onChange,
  label,
  type = "number",
  min,
  max,
}: ParamInputProps) {
  const [errors, setErrors] = useState<string[]>([])
  const [isValid, setIsValid] = useState<boolean | null>(null)
  const [isValidating, setIsValidating] = useState(false)

  useEffect(() => {
    const validateParam = async () => {
      if (paramValue === "" || paramValue === null || paramValue === undefined) {
        setErrors([])
        setIsValid(null)
        return
      }

      setIsValidating(true)
      try {
        const result = await backtestApi.validateParams({
          strategy_id: strategyId,
          params: { [paramName]: paramValue },
        })
        setIsValid(result.valid)
        setErrors(result.errors)
      } catch (error) {
        setIsValid(false)
        setErrors(["验证失败"])
      } finally {
        setIsValidating(false)
      }
    }

    const timer = setTimeout(validateParam, 500)
    return () => clearTimeout(timer)
  }, [strategyId, paramName, paramValue])

  return (
    <div className="space-y-2">
      <Label htmlFor={paramName} className="text-neutral-300">
        {label || paramName}
      </Label>
      <div className="relative">
        <Input
          id={paramName}
          type={type}
          value={paramValue}
          onChange={(e) => {
            const value = type === "number" ? parseFloat(e.target.value) : e.target.value
            onChange(paramName, value)
          }}
          min={min}
          max={max}
          className={`bg-neutral-900 border-neutral-700 text-white pr-10 ${
            isValid === false ? "border-red-500" : isValid === true ? "border-green-500" : ""
          }`}
        />
        <div className="absolute right-3 top-1/2 -translate-y-1/2">
          {isValidating ? (
            <div className="w-4 h-4 border-2 border-orange-500 border-t-transparent rounded-full animate-spin" />
          ) : isValid === true ? (
            <CheckCircle className="w-4 h-4 text-green-500" />
          ) : isValid === false ? (
            <AlertCircle className="w-4 h-4 text-red-500" />
          ) : null}
        </div>
      </div>
      {errors.length > 0 && (
        <div className="space-y-1">
          {errors.map((error, index) => (
            <p key={index} className="text-xs text-red-400 flex items-center gap-1">
              <AlertCircle className="w-3 h-3" />
              {error}
            </p>
          ))}
        </div>
      )}
    </div>
  )
}

interface ParamFormProps {
  strategyId: string
  params: Record<string, any>
  onChange: (params: Record<string, any>) => void
}

export function ParamForm({ strategyId, params, onChange }: ParamFormProps) {
  const handleParamChange = (name: string, value: any) => {
    onChange({ ...params, [name]: value })
  }

  return (
    <div className="space-y-4">
      <ParamInput
        strategyId={strategyId}
        paramName="initial_capital"
        paramValue={params.initial_capital || 500000}
        onChange={handleParamChange}
        label="初始资金"
        min={10000}
      />
      <ParamInput
        strategyId={strategyId}
        paramName="slippage_per_unit"
        paramValue={params.slippage_per_unit || 1}
        onChange={handleParamChange}
        label="滑点（每单位）"
        min={0}
      />
      <ParamInput
        strategyId={strategyId}
        paramName="commission_per_lot_round_turn"
        paramValue={params.commission_per_lot_round_turn || 8}
        onChange={handleParamChange}
        label="手续费（每手往返）"
        min={0}
      />
      <ParamInput
        strategyId={strategyId}
        paramName="timeframe_minutes"
        paramValue={params.timeframe_minutes || 60}
        onChange={handleParamChange}
        label="时间周期（分钟）"
        min={1}
        max={1440}
      />
    </div>
  )
}
