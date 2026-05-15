import Nav from '@/components/landing/Nav';
import Hero from '@/components/landing/Hero';
import StatsBar from '@/components/landing/StatsBar';
import About from '@/components/landing/About';
import HowItWorks from '@/components/landing/HowItWorks';
import TestTypeGrid from '@/components/landing/TestTypeGrid';
import Footer from '@/components/landing/Footer';

export default function Home() {
  return (
    <>
      <Nav />
      <main>
        <Hero />
        <StatsBar />
        <About />
        <HowItWorks />
        <TestTypeGrid />
      </main>
      <Footer />
    </>
  );
}
