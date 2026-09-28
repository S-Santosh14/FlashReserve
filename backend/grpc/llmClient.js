const path = require("path");

const grpc = require("@grpc/grpc-js");
const protoLoader = require("@grpc/proto-loader");

const protoPath = path.join(__dirname, "llm.proto");
const packageDefinition = protoLoader.loadSync(protoPath, { keepCase: false, longs: String, enums: String, defaults: true, oneofs: true });
const grpcPackage = grpc.loadPackageDefinition(packageDefinition).flashreserve.llm;

const address = process.env.LLM_GRPC_ADDRESS || "127.0.0.1:50051";
const client = new grpcPackage.LLMService(address, grpc.credentials.createInsecure());

function checkReady() {
  return new Promise((resolve, reject) => {
    client.waitForReady(new Date(Date.now() + 1500), (error) => {
      if (error) return reject(error);
      return resolve(true);
    });
  });
}

function askQuestion(question) {
  return new Promise((resolve, reject) => {
    client.AskQuestion(question, new grpc.Metadata(), { deadline: new Date(Date.now() + 5000) }, (error, response) => {
      if (error) return reject(error);
      return resolve(response);
    });
  });
}

module.exports = { askQuestion, checkReady, address };