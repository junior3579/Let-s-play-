# Integração do Firebase

Este projeto foi integrado com **Firebase** para autenticação e banco de dados em tempo real usando **Cloud Firestore**.

## Configuração

### Credenciais do Firebase

O Firebase foi configurado com o seguinte projeto:
- **Project ID:** lets-play-d141e
- **Auth Domain:** lets-play-d141e.firebaseapp.com
- **Storage Bucket:** lets-play-d141e.firebasestorage.app

As credenciais estão armazenadas em `/frontend-src/lib/firebase.js`.

## Serviços Utilizados

### 1. Firebase Authentication

Gerencia o login e registro de usuários. Suporta:
- Email e senha
- Provedores de terceiros (Google, Facebook, etc.)

**Hook disponível:** `useAuth()`

```javascript
import { useAuth } from '@/hooks/useAuth';

const { user, loading, error, register, login, logout } = useAuth();
```

### 2. Cloud Firestore

Banco de dados NoSQL em tempo real. Armazena dados em coleções e documentos.

**Hook disponível:** `useFirestore(collectionName)`

```javascript
import { useFirestore } from '@/hooks/useFirestore';

const { loading, error, addDocument, updateDocument, deleteDocument, getDocuments, subscribeToDocuments } = useFirestore('users');
```

## Estrutura de Dados Recomendada

### Coleção: `users`
```javascript
{
  id: "user_id",
  email: "user@example.com",
  displayName: "User Name",
  createdAt: Timestamp,
  updatedAt: Timestamp
}
```

### Coleção: `games` (exemplo para apostas)
```javascript
{
  id: "game_id",
  title: "Game Title",
  description: "Game Description",
  createdBy: "user_id",
  createdAt: Timestamp,
  updatedAt: Timestamp,
  status: "active" | "completed" | "cancelled"
}
```

## Regras de Segurança do Firestore

Para configurar as regras de segurança, acesse o Firebase Console e vá para **Firestore Database > Rules**.

### Exemplo de Regra Básica

```javascript
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    // Permitir leitura e escrita apenas para usuários autenticados
    match /{document=**} {
      allow read, write: if request.auth != null;
    }
    
    // Permitir que usuários editem apenas seus próprios dados
    match /users/{userId} {
      allow read, write: if request.auth.uid == userId;
    }
  }
}
```

## Migrando do Supabase

O Supabase foi removido do projeto. Se você tinha dados no Supabase, será necessário:

1. Exportar os dados do Supabase (geralmente em JSON ou CSV)
2. Transformar os dados para o formato do Firestore
3. Importar os dados para o Firestore usando o Firebase Console ou um script

## Variáveis de Ambiente

Não há necessidade de variáveis de ambiente para o Firebase, pois as credenciais estão no arquivo `firebase.js`. No entanto, se preferir usar variáveis de ambiente, você pode:

```javascript
// .env.local
VITE_FIREBASE_API_KEY=AIzaSyCcctMyFYwC_gfWfvsKCP9E20NTZSq-R3M
VITE_FIREBASE_AUTH_DOMAIN=lets-play-d141e.firebaseapp.com
VITE_FIREBASE_PROJECT_ID=lets-play-d141e
VITE_FIREBASE_STORAGE_BUCKET=lets-play-d141e.firebasestorage.app
VITE_FIREBASE_MESSAGING_SENDER_ID=716651655680
VITE_FIREBASE_APP_ID=1:716651655680:web:f6c348642ef37554395ee5
```

## Recursos Úteis

- [Documentação do Firebase](https://firebase.google.com/docs)
- [Cloud Firestore Documentation](https://firebase.google.com/docs/firestore)
- [Firebase Authentication Documentation](https://firebase.google.com/docs/auth)
- [Firebase Console](https://console.firebase.google.com)

## Próximos Passos

1. Configure as **Regras de Segurança** no Firebase Console
2. Crie as **Coleções** necessárias no Firestore
3. Implemente a **Autenticação** na sua aplicação
4. Integre o **Firestore** com seus componentes React
