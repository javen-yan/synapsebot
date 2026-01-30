import { Inter } from "next/font/google";
import "@/app/globals.css";
import Link from "next/link";
import { MessageSquare, Wrench, Boxes } from "lucide-react";
import { NextIntlClientProvider } from 'next-intl';
import { getMessages, getTranslations } from 'next-intl/server';

const inter = Inter({ subsets: ["latin"] });

export async function generateMetadata({params}: {params: {locale: string}}) {
  const {locale} = await params;
  const t = await getTranslations({locale, namespace: 'Layout'});
 
  return {
    title: t('title'),
    description: t('subtitle')
  };
}

export default async function RootLayout({
  children,
  params
}: Readonly<{
  children: React.ReactNode;
  params: { locale: string };
}>) {
  const { locale } = await params;
  const messages = await getMessages();
  const t = await getTranslations({locale, namespace: 'Layout'});

  return (
    <html lang={locale} className="dark">
      <body className={`${inter.className} bg-slate-950 text-slate-50`}>
        <NextIntlClientProvider messages={messages}>
          <div className="flex h-screen">
            {/* Sidebar */}
            <aside className="w-64 bg-slate-900 border-r border-slate-700 flex flex-col">
              <div className="p-6 border-b border-slate-700">
                <h1 className="text-2xl font-bold bg-gradient-to-r from-cyan-400 to-blue-500 bg-clip-text text-transparent">
                  {t('title')}
                </h1>
                <p className="text-sm text-slate-400 mt-1">
                  {t('subtitle')}
                </p>
              </div>

              <nav className="flex-1 p-4 space-y-2">
                <NavLink href={`/${locale}`} icon={<MessageSquare size={20} />}>
                  {t('nav.chat')}
                </NavLink>
                <NavLink href={`/${locale}/skills`} icon={<Boxes size={20} />}>
                  {t('nav.skills')}
                </NavLink>
                <NavLink href={`/${locale}/tools`} icon={<Wrench size={20} />}>
                  {t('nav.tools')}
                </NavLink>
              </nav>

              <div className="p-4 border-t border-slate-700 text-xs text-slate-500">
                <p>{t('version', {version: '0.1.0'})}</p>
                <div className="mt-2 flex gap-2">
                  <Link href="/en" className={`hover:text-cyan-400 ${locale === 'en' ? 'text-cyan-400 font-bold' : ''}`}>EN</Link>
                  <span>/</span>
                  <Link href="/zh" className={`hover:text-cyan-400 ${locale === 'zh' ? 'text-cyan-400 font-bold' : ''}`}>中文</Link>
                </div>
              </div>
            </aside>

            {/* Main Content */}
            <main className="flex-1 overflow-auto bg-slate-950">{children}</main>
          </div>
        </NextIntlClientProvider>
      </body>
    </html>
  );
}

function NavLink({
  href,
  icon,
  children,
}: {
  href: string;
  icon: React.ReactNode;
  children: React.ReactNode;
}) {
  return (
    <Link
      href={href}
      className="flex items-center gap-3 px-4 py-3 rounded-lg hover:bg-slate-800 transition-colors text-slate-300 hover:text-white"
    >
      {icon}
      <span>{children}</span>
    </Link>
  );
}


