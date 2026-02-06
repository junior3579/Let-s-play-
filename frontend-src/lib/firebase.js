import { initializeApp } from 'firebase/app';
import { getAuth } from 'firebase/auth';
import { getFirestore } from 'firebase/firestore';

const firebaseConfig = {
  apiKey: "AIzaSyCcctMyFYwC_gfWfvsKCP9E20NTZSq-R3M",
  authDomain: "lets-play-d141e.firebaseapp.com",
  projectId: "lets-play-d141e",
  storageBucket: "lets-play-d141e.firebasestorage.app",
  messagingSenderId: "716651655680",
  appId: "1:716651655680:web:f6c348642ef37554395ee5",
  measurementId: "G-5SMG7G1QN3"
};

// Initialize Firebase
const app = initializeApp(firebaseConfig);

// Initialize Firebase Authentication and get a reference to the service
export const auth = getAuth(app);

// Initialize Cloud Firestore and get a reference to the service
export const db = getFirestore(app);

export default app;
