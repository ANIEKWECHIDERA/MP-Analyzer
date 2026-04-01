const DB_NAME = "mp-analyzer";
const STORE_NAME = "profile-uploads";

type StoredUpload = {
  profileId: number;
  file: Blob;
  name: string;
  type: string;
  lastModified: number;
};

const openDatabase = (): Promise<IDBDatabase> =>
  new Promise((resolve, reject) => {
    const request = window.indexedDB.open(DB_NAME, 1);
    request.onupgradeneeded = () => {
      const database = request.result;
      if (!database.objectStoreNames.contains(STORE_NAME)) {
        database.createObjectStore(STORE_NAME, { keyPath: "profileId" });
      }
    };
    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error);
  });

const withStore = async <T>(
  mode: IDBTransactionMode,
  executor: (store: IDBObjectStore, resolve: (value: T) => void, reject: (reason?: unknown) => void) => void
): Promise<T> => {
  const database = await openDatabase();
  return new Promise<T>((resolve, reject) => {
    const transaction = database.transaction(STORE_NAME, mode);
    const store = transaction.objectStore(STORE_NAME);
    executor(store, resolve, reject);
    transaction.oncomplete = () => database.close();
    transaction.onerror = () => {
      database.close();
      reject(transaction.error);
    };
  });
};

export const saveUploadForProfile = async (profileId: number, file: File) => {
  await withStore<void>("readwrite", (store, resolve, reject) => {
    const request = store.put({
      profileId,
      file,
      name: file.name,
      type: file.type,
      lastModified: file.lastModified,
    } satisfies StoredUpload);
    request.onsuccess = () => resolve();
    request.onerror = () => reject(request.error);
  });
};

export const loadUploadForProfile = async (profileId: number): Promise<File | null> =>
  withStore<File | null>("readonly", (store, resolve, reject) => {
    const request = store.get(profileId);
    request.onsuccess = () => {
      const result = request.result as StoredUpload | undefined;
      if (!result) {
        resolve(null);
        return;
      }
      resolve(
        new File([result.file], result.name, {
          type: result.type,
          lastModified: result.lastModified,
        })
      );
    };
    request.onerror = () => reject(request.error);
  });

export const clearUploadForProfile = async (profileId: number) => {
  await withStore<void>("readwrite", (store, resolve, reject) => {
    const request = store.delete(profileId);
    request.onsuccess = () => resolve();
    request.onerror = () => reject(request.error);
  });
};
