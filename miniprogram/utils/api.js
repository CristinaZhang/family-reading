const { BASE_URL } = require("./config");

function getToken() {
  return wx.getStorageSync("access_token") || "";
}

function request(method, path, data) {
  return new Promise((resolve, reject) => {
    wx.request({
      url: `${BASE_URL}${path}`,
      method,
      data,
      header: {
        "Content-Type": "application/json",
        Authorization: getToken() ? `Bearer ${getToken()}` : "",
      },
      success: (res) => {
        if (res.statusCode >= 200 && res.statusCode < 300) return resolve(res.data);
        reject(res);
      },
      fail: reject,
    });
  });
}

module.exports = {
  request,
};

