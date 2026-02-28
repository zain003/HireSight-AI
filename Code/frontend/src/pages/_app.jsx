/**
 * Next.js App Component
 */
import '@/styles/globals.css';
import Head from 'next/head';

export default function App({ Component, pageProps }) {
  return (
    <>
      <Head>
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <meta name="description" content="HireSIGHT AI — AI-Powered Interview Preparation Platform" />
        <title>HireSIGHT AI</title>
      </Head>
      <div className="font-sans antialiased">
        <Component {...pageProps} />
      </div>
    </>
  );
}
