export class AdapterEndpoint {
    constructor(adapter, base_url = '', api_version = '0.1') {
      this.adapter = adapter;
      this.api_version = api_version;
      this.base_url = base_url.replace(/\/$/, '');
    }
  
    build_url(path = '') {
      const cleanedPath = path ? `/${path}` : '';
      return `${this.base_url}/api/${this.api_version}/${this.adapter}${cleanedPath}`;
    }
  
    async get(path = '') {
      const url = this.build_url(path);
      const response = await fetch(url, {
        method: 'GET',
        headers: { 'Accept': 'application/json' },
      });
  
      if (!response.ok) {
        let message;
        try {
          const err = await response.json();
          message = err.error || `GET request to ${url} failed with status ${response.status}`;
        } catch {
          message = `GET request to ${url} failed with status ${response.status}`;
        }
        throw new Error(message);
      }
  
      return await response.json();
    }
  
    async put(data, path = '') {
      const url = this.build_url(path);
      const response = await fetch(url, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
        },
        body: JSON.stringify(data),
      });
  
      if (!response.ok) {
        let message;
        try {
          const err = await response.json();
          message = err.error || `PUT request to ${url} failed with status ${response.status}`;
        } catch {
          message = `PUT request to ${url} failed with status ${response.status}`;
        }
        throw new Error(message);
      }
  
      return await response.json();
    }
  }
  