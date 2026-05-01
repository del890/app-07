import type { VariantProps } from "class-variance-authority"
import { cva } from "class-variance-authority"

export { default as Button } from "./Button.vue"

export const buttonVariants = cva(
  "inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-md text-sm font-medium ring-offset-background transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 [&_svg]:pointer-events-none [&_svg]:size-4 [&_svg]:shrink-0",
  {
    variants: {
      variant: {
        default: "bg-primary/90 backdrop-blur-sm text-primary-foreground hover:bg-primary border border-primary/20 shadow-sm",
        destructive:
          "bg-destructive/85 backdrop-blur-sm text-destructive-foreground hover:bg-destructive/95 border border-destructive/20 shadow-sm",
        outline:
          "border border-input bg-background/60 backdrop-blur-sm hover:bg-accent/70 hover:text-accent-foreground",
        secondary:
          "bg-secondary/70 backdrop-blur-sm text-secondary-foreground hover:bg-secondary/90 border border-secondary/20",
        ghost: "hover:bg-accent/60 hover:backdrop-blur-sm hover:text-accent-foreground",
        link: "text-primary underline-offset-4 hover:underline",
      },
      size: {
        "default": "h-10 px-4 py-2",
        "sm": "h-9 rounded-md px-3",
        "lg": "h-11 rounded-md px-8",
        "icon": "h-10 w-10",
        "icon-sm": "size-9",
        "icon-lg": "size-11",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  },
)

export type ButtonVariants = VariantProps<typeof buttonVariants>
