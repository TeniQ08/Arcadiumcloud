import {
  Benefits,
  Features,
  FinalCTA,
  Footer,
  Hero,
  HowItWorks,
  Navbar,
  PricingTeaser,
  Problem,
  Solution,
  Testimonials,
  TrustStrip,
  WhoItsFor
} from "@/components/landing";

export default function Page() {
  return (
    <div className="min-h-dvh">
      <Navbar />
      <main>
        <Hero />
        <TrustStrip />
        <Problem />
        <Solution />
        <Features />
        <HowItWorks />
        <Benefits />
        <WhoItsFor />
        <PricingTeaser />
        <Testimonials />
        <FinalCTA />
      </main>
      <Footer />
    </div>
  );
}

