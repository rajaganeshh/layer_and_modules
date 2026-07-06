

module.exports.pythonApi = async (data) => {
  try {
    let result;
    const options = {
      headers: {
        "Content-Type": "application/json",
      },
    };
    if (data.method === "get") {
      const response = await fetch(
        `${!data.url?JSON.parse(process.env.secrets).app.BASE_URL:data.url}` + data.endpoint,
        options
      );

      result = await response.json();
      if (!response.ok) {
        const error = {
          status: response.status,
          error: result.message,
        };
        throw error;
      }
    }

    if (data.method === "post") {
      options["method"] = "POST";
      options["body"] = JSON.stringify(data.payload);
      response = await fetch(`${!data.url?JSON.parse(process.env.secrets).app.BASE_URL:data.url}` + data.endpoint, options);
      result = await response.json();
      if (!response.ok) {
        const error = {
          status: response.status,
          error: result.message,
        };
        throw error;
      }
    }
    return result;
  } catch (error) {
    throw error;
  }
};
