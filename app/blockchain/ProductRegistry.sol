// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

contract ProductRegistry {
    
    struct Product {
        uint256 tokenId;
        string productCode;
        string metadataURI;
        address creator;
        address currentOwner;
        uint256 createdAt;
        bool exists;
    }
    
    string public name = "TraceableProduct";
    string public symbol = "TPROD";
    uint256 private _tokenIdCounter;
    address public owner;
    
    mapping(uint256 => Product) private products;
    mapping(string => uint256) private productCodeToTokenId;
    
    event ProductMinted(uint256 indexed tokenId, string productCode, address indexed creator);
    event OwnershipTransferred(uint256 indexed tokenId, address indexed from, address indexed to, uint256 price);
    
    modifier onlyOwner() {
        require(msg.sender == owner, "Not owner");
        _;
    }
    
    constructor() {
        owner = msg.sender;
        _tokenIdCounter = 1;
    }
    
    function mintProduct(string memory productCode, string memory metadataURI, address creator) 
        external onlyOwner returns (uint256) 
    {
        require(bytes(productCode).length > 0, "Code required");
        require(productCodeToTokenId[productCode] == 0, "Already minted");
        require(creator != address(0), "Invalid creator");
        
        uint256 tokenId = _tokenIdCounter;
        _tokenIdCounter++;
        
        products[tokenId] = Product(tokenId, productCode, metadataURI, creator, creator, block.timestamp, true);
        productCodeToTokenId[productCode] = tokenId;
        
        emit ProductMinted(tokenId, productCode, creator);
        return tokenId;
    }
    
    function transferOwnership(uint256 tokenId, address to, uint256 price) 
        external onlyOwner 
    {
        require(products[tokenId].exists, "Not found");
        require(to != address(0), "Invalid recipient");
        require(products[tokenId].currentOwner != to, "Self transfer");
        
        address from = products[tokenId].currentOwner;
        products[tokenId].currentOwner = to;
        
        emit OwnershipTransferred(tokenId, from, to, price);
    }
    
    function getProduct(uint256 tokenId) external view returns (
        uint256 id, string memory code, string memory uri, 
        address creator, address currentOwner, uint256 createdAt, bool exists
    ) {
        Product memory p = products[tokenId];
        return (p.tokenId, p.productCode, p.metadataURI, p.creator, p.currentOwner, p.createdAt, p.exists);
    }
    
    function getProductByCode(string memory productCode) external view returns (
        uint256 id, string memory uri, address creator, address currentOwner, uint256 createdAt
    ) {
        uint256 tokenId = productCodeToTokenId[productCode];
        require(tokenId > 0, "Not found");
        Product memory p = products[tokenId];
        return (p.tokenId, p.metadataURI, p.creator, p.currentOwner, p.createdAt);
    }
    
    function verifyProduct(uint256 tokenId) external view returns (bool valid, address creator, address currentOwner) {
        require(products[tokenId].exists, "Not found");
        Product memory p = products[tokenId];
        return (true, p.creator, p.currentOwner);
    }
    
    function totalSupply() external view returns (uint256) {
        return _tokenIdCounter - 1;
    }
}
