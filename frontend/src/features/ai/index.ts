import aiClient from './api';
import useAI from './hooks';

export * from './api';
export * from './hooks';

export {
  aiClient,
  useAI
};

export default { 
  client: aiClient,
  useAI
};