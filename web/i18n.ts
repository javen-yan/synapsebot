import {notFound} from 'next/navigation';
import {getRequestConfig} from 'next-intl/server';
 
// Can be imported from a shared config
const locales = ['en', 'zh'];
 
export default getRequestConfig(async ({requestLocale}) => {
  // Validate that the incoming `locale` parameter is valid
  let locale = await requestLocale;
  if (!locale || !locales.includes(locale as any)) {
      locale = 'en'; // Fallback or handle error
  }
 
  return {
    locale,
    messages: (await import(`./messages/${locale}.json`)).default
  };
});
