import { useCallback, useState } from 'react';
import {
  collection,
  addDoc,
  updateDoc,
  deleteDoc,
  doc,
  getDocs,
  query,
  where,
  orderBy,
  limit,
  onSnapshot,
} from 'firebase/firestore';
import { db } from '@/lib/firebase';

export const useFirestore = (collectionName) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const addDocument = useCallback(
    async (data) => {
      try {
        setLoading(true);
        setError(null);
        const docRef = await addDoc(collection(db, collectionName), {
          ...data,
          createdAt: new Date(),
        });
        return docRef.id;
      } catch (err) {
        setError(err.message);
        throw err;
      } finally {
        setLoading(false);
      }
    },
    [collectionName]
  );

  const updateDocument = useCallback(
    async (docId, data) => {
      try {
        setLoading(true);
        setError(null);
        const docRef = doc(db, collectionName, docId);
        await updateDoc(docRef, {
          ...data,
          updatedAt: new Date(),
        });
      } catch (err) {
        setError(err.message);
        throw err;
      } finally {
        setLoading(false);
      }
    },
    [collectionName]
  );

  const deleteDocument = useCallback(
    async (docId) => {
      try {
        setLoading(true);
        setError(null);
        await deleteDoc(doc(db, collectionName, docId));
      } catch (err) {
        setError(err.message);
        throw err;
      } finally {
        setLoading(false);
      }
    },
    [collectionName]
  );

  const getDocuments = useCallback(
    async (constraints = []) => {
      try {
        setLoading(true);
        setError(null);
        const q = query(collection(db, collectionName), ...constraints);
        const snapshot = await getDocs(q);
        return snapshot.docs.map((doc) => ({
          id: doc.id,
          ...doc.data(),
        }));
      } catch (err) {
        setError(err.message);
        throw err;
      } finally {
        setLoading(false);
      }
    },
    [collectionName]
  );

  const subscribeToDocuments = useCallback(
    (callback, constraints = []) => {
      try {
        setError(null);
        const q = query(collection(db, collectionName), ...constraints);
        const unsubscribe = onSnapshot(q, (snapshot) => {
          const documents = snapshot.docs.map((doc) => ({
            id: doc.id,
            ...doc.data(),
          }));
          callback(documents);
        });
        return unsubscribe;
      } catch (err) {
        setError(err.message);
        throw err;
      }
    },
    [collectionName]
  );

  return {
    loading,
    error,
    addDocument,
    updateDocument,
    deleteDocument,
    getDocuments,
    subscribeToDocuments,
  };
};
