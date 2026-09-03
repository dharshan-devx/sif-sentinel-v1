const testFetch = async () => {
  try {
    const res1 = await fetch("http://localhost:8000/api/v1/health");
    console.log("localhost:", res1.status, await res1.text());
  } catch (e) {
    console.error("localhost ERROR:", e.message);
  }

  try {
    const res2 = await fetch("http://127.0.0.1:8000/api/v1/health");
    console.log("127.0.0.1:", res2.status, await res2.text());
  } catch (e) {
    console.error("127.0.0.1 ERROR:", e.message);
  }
};

testFetch();
