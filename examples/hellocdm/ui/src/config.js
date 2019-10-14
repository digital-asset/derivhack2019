import uuidv4 from "uuid/v4";
import * as jwt from "jsonwebtoken";

const isLocalDev = true;
const continuousUpdate = false;
const localLedgerId = "hellocdm"
const applicationId = "HTTP-JSON-API-Gateway"
const createToken = party => jwt.sign({ "ledgerId": localLedgerId, "applicationId": applicationId, "party": party }, "secret")
const parties = [ "Alice" ];

// Dev config
const localConfig = {
  isLocalDev,
  continuousUpdate,
  tokens: {}
}
parties.map(p => localConfig.tokens[p] = createToken(p));

// DABL config
const dablConfig = {
  isLocalDev,
  continuousUpdate,
  tokens: {
    Alice: "eyJhbGciOiJSUzI1NiIsImtpZCI6ImRhYmwtMjAxOS0xMC0wNC0yMDUyMDYiLCJ0eXAiOiJKV1QifQ.eyJhdWQiOlsicHJvamVjdGRhYmwiXSwiZGFibExlZGdlclBhcnR5IjoiYml3aGI5M2oxd3BjN2M1dCIsImRhYmxMZWRnZXJSaWdodHMiOlsicmVhZCIsIndyaXRlOmNyZWF0ZSIsIndyaXRlOmV4ZXJjaXNlIl0sImVtYWlsIjoiZGltaXRyaS5saWFrYWtvc0BkaWdpdGFsYXNzZXQuY29tIiwiZW1haWxfdmVyaWZpZWQiOnRydWUsImV4cCI6MTU3MDU1NzI0MywiaWF0IjoxNTcwNDcwODQzLCJpc3MiOiJwcm9qZWN0ZGFibC1zaXRlIiwianRpIjoiSFpfMkZuUkFOV1pGMzQzQnkxSTZiZyIsIm5hbWUiOiJEaW1pdHJpIExpYWtha29zIiwibmJmIjoxNTcwNDcwODQzLCJuaWNrbmFtZSI6ImRpbWl0cmkubGlha2Frb3MiLCJwaWN0dXJlIjoiaHR0cHM6Ly9saDMuZ29vZ2xldXNlcmNvbnRlbnQuY29tL2EtL0FBdUU3bUN2b08xYlRRWlNJZlR1V3d2SE91SU5xdkoyYVc1cFhURDlkM0I1Iiwic3ViIjoiZ29vZ2xlLWFwcHN8ZGltaXRyaS5saWFrYWtvc0BkaWdpdGFsYXNzZXQuY29tIiwidG9zQWNjZXB0ZWQiOnRydWV9.NwobjWM5a8IoVsADAfopUxA-AMCJpoQKFKtXN4LzUlIwHdsUTF5XIJEm9sq_TZ_XOJv-LDkjVinxs0Vt3WpT-3RDTVJTx6pRo6cu2hddkj3wmufK5p3iLmYaaICpJ-cjl4eDx4IbtANoeVzYj5pzU3n01ZOnULZ7PeQRZ8KUiMqbe99jxfGDRIqCX7O-zCO6q9Cj31aIL1wpbRLLuhEG1kCGQrRoLr2yETc_d7TusNumVjhRhIzmH7HaZge3-08LEqdznBPYgcjbj9WXer2VxXps4Wx9hhBgdv7mvOOeFUUI8poRGjjlDZ7wCPBIP_0Ca1FX-wDX6M4CY9YnTCzbKg" // Copy token for Alice from DABL website
  }
}

const config = isLocalDev ? localConfig : dablConfig
export default config;
