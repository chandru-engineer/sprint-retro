export function HeroBlurShapes() {
  return (
    <div aria-hidden="true" className="pointer-events-none absolute inset-0 overflow-hidden rounded-[inherit]">
      <div className="absolute -top-24 -left-24 h-96 w-96 rounded-full bg-md-primary/25 blur-3xl mix-blend-multiply" />
      <div className="absolute -bottom-32 -right-16 h-[28rem] w-[28rem] rounded-full bg-md-tertiary/20 blur-3xl mix-blend-multiply" />
      <div className="absolute top-1/3 right-1/4 h-64 w-64 rounded-full bg-md-secondary/20 blur-3xl mix-blend-multiply" />
    </div>
  );
}

export function SectionBlurShapes() {
  return (
    <div aria-hidden="true" className="pointer-events-none absolute inset-0 overflow-hidden rounded-[inherit]">
      <div className="absolute top-0 right-0 h-72 w-72 translate-x-1/4 -translate-y-1/3 rounded-full bg-md-primary/20 blur-3xl mix-blend-multiply" />
      <div className="absolute bottom-0 left-0 h-80 w-80 -translate-x-1/4 translate-y-1/3 rounded-full bg-md-tertiary/20 blur-3xl mix-blend-multiply" />
    </div>
  );
}
